"""Integração de hardware testada sem credenciais nem envios remotos."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
from fastapi.testclient import TestClient

from app.backend import ibm_runtime, service
from app.backend.api import app
from app.backend.schemas import ClassicalRequest, HardwareRequest, QuantumRequest
from app.backend.storage import RunStore
from neutrinos.sim import ExperimentConfig


class IbmRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_store = service.store
        service.store = RunStore(Path(self.temp.name))

    def tearDown(self):
        service.store = self.original_store
        self.temp.cleanup()

    def test_env_status_never_returns_key(self):
        with patch.dict(os.environ, {"IBM_QUANTUM_API_KEY": "secret-for-test",
                                     "IBM_QUANTUM_INSTANCE": "crn:test"}):
            status = ibm_runtime.status()
        self.assertTrue(status["configured"])
        self.assertTrue(status["instance_configured"])
        self.assertNotIn("secret-for-test", json.dumps(status))

    def test_qiskit_sampler_receives_transpiled_circuit_without_network(self):
        from qiskit_ibm_runtime.fake_provider import FakeBelemV2

        backend = FakeBelemV2()
        cloud = Mock()
        cloud.backend.return_value = backend
        sampler = Mock()
        sampler.run.return_value.job_id.return_value = "offline-job"
        request = HardwareRequest(backend="fake_belem", interval_index=1,
                                  steps=1, shots=32)
        with patch.object(ibm_runtime, "_service", return_value=cloud), patch(
                "qiskit_ibm_runtime.executor_sampler.Sampler", return_value=sampler):
            submitted = ibm_runtime.submit(
                ExperimentConfig(n=2, flavors=(0, 1), t_max=1, points=3), request)
        self.assertEqual(submitted["job_id"], "offline-job")
        circuit = sampler.run.call_args.args[0][0]
        self.assertEqual(circuit.num_clbits, 2)
        self.assertEqual(sampler.run.call_args.kwargs["shots"], 32)
        self.assertGreater(submitted["transpiled_depth"], 0)
        from qiskit import qpy
        circuit_bytes = base64.b64decode(submitted["circuit_qpy_base64"])
        archived = qpy.load(io.BytesIO(circuit_bytes))[0]
        self.assertEqual(archived.num_clbits, 2)
        self.assertEqual(submitted["circuit_sha256"], hashlib.sha256(circuit_bytes).hexdigest())
        self.assertIn("backend_properties", submitted)

    def test_short_circuit_options_are_applied_and_archived_without_network(self):
        from qiskit_ibm_runtime.fake_provider import FakeBelemV2

        cloud = Mock()
        cloud.backend.return_value = FakeBelemV2()
        sampler = MagicMock()
        sampler.run.return_value.job_id.return_value = "short-offline-job"
        request = HardwareRequest(backend="fake_belem", interval_index=1,
                                  steps=2, shots=32, optimization_level=3,
                                  gate_twirling=True, dynamical_decoupling=True)
        with patch.object(ibm_runtime, "_service", return_value=cloud), patch(
                "qiskit_ibm_runtime.executor_sampler.Sampler", return_value=sampler):
            result = ibm_runtime.submit(ExperimentConfig(n=2, flavors=(0, 1),
                                        t_max=1.5, points=2), request)
        self.assertEqual(result["transpilation"]["optimization_level"], 3)
        self.assertTrue(result["runtime_options"]["gate_twirling"])
        self.assertTrue(result["runtime_options"]["dynamical_decoupling"])
        self.assertTrue(sampler.options.twirling.enable_gates)
        self.assertTrue(sampler.options.dynamical_decoupling.enable)
        self.assertEqual(sampler.run.call_args.kwargs["shots"], 32)

    def test_qiskit_counts_keep_qubit_bit_order(self):
        cloud = MagicMock()
        job = cloud.job.return_value
        job.status.return_value = "DONE"
        job.result.return_value.__getitem__.return_value.data.meas.get_counts.return_value = {
            "00": 10, "01": 22,
        }
        with patch.object(ibm_runtime, "_service", return_value=cloud):
            state, counts = ibm_runtime.fetch("offline-job", 2)
        self.assertEqual(state, "DONE")
        self.assertEqual(counts.tolist(), [10, 22, 0, 0])

    def test_hardware_circuit_and_calibration_are_saved_without_remote_submission(self):
        from qiskit import qpy
        from qiskit_ibm_runtime.fake_provider import FakeBelemV2

        created = service.create_experiment(ClassicalRequest(config={
            "n": 2, "flavors": [0, 1], "t_max": .2, "points": 3, "seed": 7,
        }, trajectories=16, substeps=1))
        service.run_quantum(created["run_id"], QuantumRequest(steps=1, shots=32))
        cloud = Mock()
        cloud.backend.return_value = FakeBelemV2()
        sampler = Mock()
        sampler.run.return_value.job_id.return_value = "archived-test-job"
        with patch.object(ibm_runtime, "_service", return_value=cloud), patch(
                "qiskit_ibm_runtime.executor_sampler.Sampler", return_value=sampler):
            submitted = service.submit_hardware(created["run_id"], HardwareRequest(
                backend="fake_belem", interval_index=1, steps=1, shots=32))
        entry = submitted["hardware_runs"][0]
        arrays = service.store.load(created["run_id"])[2]
        encoded = arrays[entry["circuit_artifact"]["array_key"]].tobytes()
        self.assertEqual(hashlib.sha256(encoded).hexdigest(), entry["circuit_artifact"]["sha256"])
        self.assertEqual(qpy.load(io.BytesIO(encoded))[0].num_clbits, 2)
        self.assertEqual(entry["transpilation"]["seed_transpiler"], 7)
        self.assertIsNotNone(entry["backend_properties"])
        manifest = service.store.load_metadata(created["run_id"])[0]
        self.assertEqual(manifest["hardware_runs"][0]["circuit_artifact"], entry["circuit_artifact"])

    def test_submitted_job_is_persisted_and_results_can_be_resumed(self):
        created = service.create_experiment(ClassicalRequest(config={
            "n": 2, "mu": 1, "theta": .2, "t_max": 1, "points": 3,
            "flavors": [0, 1], "seed": 7,
        }, trajectories=16, substeps=1))
        run_id = created["run_id"]
        service.run_quantum(run_id, QuantumRequest(steps=1, shots=32, readout_error=0))
        request = HardwareRequest(backend="ibm_test", interval_index=1,
                                  steps=1, shots=32, kind="pe", index=0)
        with patch.object(ibm_runtime, "submit", return_value={
            "job_id": "test-job-123", "backend": "ibm_test",
            "transpiled_depth": 12, "two_qubit_gates": 3,
        }), patch.object(ibm_runtime, "fetch", return_value=(
            "QUEUED", None)) as fetch:
            submitted = service.submit_hardware(run_id, request)
            self.assertEqual(submitted["hardware_runs"][0]["status"], "QUEUED")
            version_before = (service.store.root / run_id / "current").read_text()
            queued = service.refresh_hardware(run_id, "test-job-123")
            self.assertIn("checked_utc", queued)
            self.assertEqual((service.store.root / run_id / "current").read_text(), version_before)
            fetch.return_value = ("DONE", np.array([8, 8, 8, 8], dtype=np.int64))
            completed = service.refresh_hardware(run_id, "test-job-123")

        self.assertEqual(completed["status"], "DONE")
        self.assertEqual(completed["estimate"], .5)
        self.assertEqual(completed["shots"], 32)
        self.assertEqual(int(service.store.load(run_id)[2]["ibm_0001_counts"].sum()), 32)
        self.assertEqual(service.refresh_hardware(run_id, "test-job-123"), completed)
        manifest, summary = service.store.load_metadata(run_id)
        self.assertEqual(summary["hardware_runs"][0]["job_id"], "test-job-123")
        self.assertEqual(manifest["hardware_runs"][0]["counts_key"], "ibm_0001_counts")
        self.assertNotIn("IBM_QUANTUM_API_KEY", json.dumps(manifest))

    def test_http_hardware_job_flow(self):
        created = service.create_experiment(ClassicalRequest(config={
            "n": 2, "flavors": [0, 1], "t_max": 1, "points": 3,
        }, trajectories=16, substeps=1))
        run_id = created["run_id"]
        service.run_quantum(run_id, QuantumRequest(steps=1, shots=32))
        with patch.object(ibm_runtime, "submit", return_value={
            "job_id": "http-job", "backend": "ibm_test", "transpiled_depth": 12,
            "two_qubit_gates": 3,
        }), patch.object(ibm_runtime, "fetch", return_value=(
            "DONE", np.array([8, 8, 8, 8], dtype=np.int64))), TestClient(app) as client:
            started = client.post(f"/api/jobs/{run_id}/hardware", json={
                "backend": "ibm_test", "interval_index": 1, "steps": 1,
                "shots": 32, "kind": "pe", "index": 0,
            })
            self.assertEqual(started.status_code, 202, started.text)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                job = client.get(f"/api/jobs/{started.json()['job_id']}").json()
                if job["status"] in {"completed", "failed"}:
                    break
                time.sleep(.02)
            self.assertEqual(job["status"], "completed", job)
            completed = client.get(f"/api/experiments/{run_id}/hardware/http-job")
            self.assertEqual(completed.status_code, 200, completed.text)
            self.assertEqual(completed.json()["estimate"], .5)


if __name__ == "__main__":
    unittest.main()
