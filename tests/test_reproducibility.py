"""Durabilidade de tentativas, integridade e reprodução numérica real."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from app.backend import audit, protocol, service
from app.backend.api import app
from app.backend.jobs import JobManager
from app.backend.schemas import AerRequest, ClassicalRequest, QuantumRequest
from app.backend.storage import RunStore


def small_protocol():
    return protocol.ProtocolSpec.model_validate({
        "schema_version": 1, "name": "three-body-test", "steps": [
            {"id": "reference", "action": "classical", "request": {
                "config": {"n": 3, "flavors": [0, 0, 1], "mu": 1,
                           "t_max": .5, "points": 5, "seed": 7},
                "trajectories": 16, "substeps": 1}},
            {"id": "circuit", "action": "quantum", "run_from": "reference",
             "request": {"steps": 1, "shots": 32, "readout_error": .01}},
            {"id": "interval", "action": "interval", "run_from": "reference",
             "request": {"method": "measured", "kind": "c3", "index": 0,
                         "repetitions": 20, "seed": 19}},
        ]})


class ReproducibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_store = service.store
        service.store = RunStore(self.root)

    def tearDown(self):
        service.store = self.old_store
        self.temp.cleanup()

    def records(self):
        return [json.loads(path.read_text()) for path in (self.root / "executions").glob("*/execution.json")]

    def test_success_has_complete_persistence_trace_and_archived_sources(self):
        result = service.create_experiment(ClassicalRequest(**small_protocol().steps[0].request))
        record = self.records()[0]
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["run_id"], result["run_id"])
        self.assertTrue(any(step["stage"] == "persist" and step["status"] == "done" for step in record["steps"]))
        self.assertEqual(record["inputs"]["request"]["config"]["seed"], 7)
        self.assertIn("app/backend/service.py", record["environment"]["source_sha256"])
        archive = self.root / record["source_snapshot"]
        self.assertTrue((archive / "requirements.txt").is_file())
        self.assertFalse((archive / ".env").exists())
        protocol.verify_artifacts(self.root, record)
        with TestClient(app) as client:
            saved = client.get(f"/api/executions/{record['execution_id']}")
            self.assertEqual(saved.json()["status"], "completed")
            history = client.get(f"/api/experiments/{result['run_id']}/executions").json()
            self.assertEqual(history[0]["execution_id"], record["execution_id"])

    def test_failure_before_run_exists_keeps_steps_and_redacts_credentials(self):
        with patch.dict(os.environ, {"IBM_QUANTUM_API_KEY": "sensitive-token"}), patch.object(
                service, "phase_space", side_effect=RuntimeError("PSA failed sensitive-token")):
            with self.assertRaises(RuntimeError):
                service.create_experiment(ClassicalRequest(**small_protocol().steps[0].request))
        record = self.records()[0]
        self.assertEqual(record["status"], "failed")
        self.assertIsNone(record["run_id"])
        self.assertTrue(any(step["stage"] == "mean" and step["status"] == "done" for step in record["steps"]))
        self.assertIn("[REDACTED]", record["error"]["message"])
        self.assertNotIn("sensitive-token", json.dumps(record))
        self.assertIsNotNone(record["finished_utc"])

    def test_full_protocol_replay_matches_three_body_samples_and_intervals(self):
        result = protocol.run_protocol(small_protocol())
        self.assertEqual(result["status"], "completed")
        execution_id = result["steps"][-1]["execution_id"]
        replayed = protocol.replay_execution(self.root / "executions" / execution_id / "execution.json")
        self.assertTrue(replayed["comparison"]["pass"])
        self.assertNotEqual(result["steps"][0]["run_id"], replayed["steps"][0]["run_id"])
        quantum_id = result["steps"][1]["execution_id"]
        repeated_quantum = protocol.replay_execution(self.root / "executions" / quantum_id / "execution.json")
        checks = repeated_quantum["comparison"]["checks"]
        self.assertTrue(repeated_quantum["comparison"]["pass"])
        self.assertTrue(any(item["artifact"] == "measured_counts" for item in checks))

    def test_resume_does_not_repeat_successful_reference(self):
        with patch.object(service, "quantum_trotter", side_effect=RuntimeError("controlled failure")):
            with self.assertRaises(protocol.ProtocolFailed) as failure:
                protocol.run_protocol(small_protocol())
        path = failure.exception.record_path
        failed = json.loads(path.read_text())
        run_id = failed["steps"][0]["run_id"]
        self.assertEqual(failed["steps"][1]["status"], "failed")
        with patch.object(service, "create_experiment", wraps=service.create_experiment) as create:
            resumed = protocol.run_protocol(small_protocol(), resume=path)
            create.assert_not_called()
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(resumed["steps"][0]["run_id"], run_id)
        self.assertEqual(len(resumed["steps"][1]["attempts"]), 2)

    def test_changed_result_is_detected_before_replay(self):
        result = protocol.run_protocol(small_protocol())
        execution = audit.load_execution(self.root, result["steps"][1]["execution_id"])
        artifact = next(item for item in execution["artifacts"] if item["path"].endswith("summary.json"))
        with (self.root / artifact["path"]).open("a") as stream:
            stream.write(" ")
        with patch.object(service, "create_experiment") as create, self.assertRaisesRegex(ValueError, "alterado"):
            protocol.replay_execution(self.root / "executions" / execution["execution_id"] / "execution.json")
        create.assert_not_called()

    def test_environment_difference_requires_explicit_override(self):
        result = protocol.run_protocol(small_protocol())
        execution_path = self.root / "executions" / result["steps"][1]["execution_id"] / "execution.json"
        saved = json.loads(execution_path.read_text())
        saved["environment"]["dependencies"]["numpy"] = "0.0.0"
        audit.atomic_json(execution_path, saved)
        with self.assertRaisesRegex(ValueError, "numpy"):
            protocol.replay_execution(execution_path)

    def test_dead_process_is_recorded_as_interrupted_with_its_last_step(self):
        result = service.create_experiment(ClassicalRequest(**small_protocol().steps[0].request))
        execution_id = audit.execution_history(self.root, result["run_id"])[0]["execution_id"]
        path = self.root / "executions" / execution_id / "execution.json"
        record = json.loads(path.read_text())
        record.update(status="running", finished_utc=None)
        audit.atomic_json(path, record)
        with patch.object(audit, "process_alive", return_value=False):
            recovered = audit.load_execution(self.root, execution_id)
        self.assertEqual(recovered["status"], "interrupted")
        self.assertEqual(recovered["error"]["type"], "ProcessInterrupted")
        self.assertEqual(recovered["steps"][-1]["status"], "failed")

    def test_remote_submission_is_never_implicit(self):
        spec = small_protocol().model_dump()
        spec["steps"].append({"id": "hardware", "action": "hardware", "run_from": "reference",
                              "request": {"backend": "ibm_example", "shots": 32, "steps": 1}})
        with patch.object(service, "submit_hardware") as submit, self.assertRaises(protocol.ProtocolFailed):
            protocol.run_protocol(protocol.ProtocolSpec.model_validate(spec))
        submit.assert_not_called()
        record = json.loads(next((self.root / "protocols").glob("*/run.json")).read_text())
        self.assertEqual(record["status"], "failed")
        self.assertIn("--allow-hardware", record["error"]["message"])

    def test_jobs_can_be_read_after_manager_is_recreated(self):
        first = JobManager()
        second = JobManager()
        self.addCleanup(first.executor.shutdown, wait=True)
        self.addCleanup(second.executor.shutdown, wait=True)
        request = ClassicalRequest(**small_protocol().steps[0].request)
        job = first.start("classical", lambda report: service.create_experiment(request, progress=report),
                          inputs=request.model_dump())
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            job = first.get(job["job_id"])
            if job["status"] in {"completed", "failed"}:
                break
            time.sleep(.01)
        recovered = second.get(job["job_id"])
        self.assertEqual(recovered["status"], "completed", recovered)
        self.assertEqual(recovered["execution_id"], job["execution_id"])
        self.assertEqual(recovered["inputs"]["config"]["seed"], 7)

    def test_aer_attempts_keep_distinct_counts_and_records(self):
        result = service.create_experiment(ClassicalRequest(**small_protocol().steps[0].request))
        request = AerRequest(interval_index=1, steps=1, shots=32, kind="c3", index=0)
        with patch.object(service, "_qiskit_worker", side_effect=[
            {"counts": [32] + [0] * 7, "metadata": {"shots": 32}},
            {"counts": [0, 32] + [0] * 6, "metadata": {"shots": 32}},
        ]):
            first = service.run_aer(result["run_id"], request)
            second = service.run_aer(result["run_id"], request)
        arrays = service.store.load(result["run_id"])[2]
        self.assertEqual(arrays[first["counts_key"]][0], 32)
        self.assertEqual(arrays[second["counts_key"]][1], 32)
        self.assertFalse(np.array_equal(arrays[first["counts_key"]], arrays[second["counts_key"]]))
        self.assertEqual(len([item for item in self.records() if item["action"] == "aer"]), 2)


if __name__ == "__main__":
    unittest.main()
