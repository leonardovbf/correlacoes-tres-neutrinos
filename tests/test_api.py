"""Fluxo HTTP e persistência de uma execução pequena e real."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.backend import service
from app.backend.api import app
from app.backend.storage import RunStore


class ApiFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_store = service.store
        service.store = RunStore(Path(self.temp.name))
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        service.store = self.original_store
        self.temp.cleanup()

    def test_full_run_and_versioned_persistence(self):
        config = {"n": 4, "mu": 1, "theta": .2, "omega_spread": .3,
                  "t_max": 2, "points": 21, "flavors": [0, 0, 1, 1], "seed": 9}
        created = self.client.post("/api/experiments", json={
            "config": config, "trajectories": 64, "substeps": 2})
        self.assertEqual(created.status_code, 201, created.text)
        run_id = created.json()["run_id"]
        self.assertEqual(len(created.json()["classical"]["exact"]["pe"]), 21)
        self.assertEqual(self.client.post(f"/api/experiments/{run_id}/interval", json={
            "method": "psa", "kind": "c3", "index": 0}).status_code, 200)

        quantum = self.client.post(f"/api/experiments/{run_id}/quantum", json={
            "steps": 2, "shots": 128, "readout_error": .02})
        self.assertEqual(quantum.status_code, 200, quantum.text)
        self.assertEqual(sum(service.store.load(run_id)[2]["measured_counts"][0]), 128)
        circuit = self.client.post(f"/api/experiments/{run_id}/circuit", json={"steps": 2})
        self.assertEqual(circuit.status_code, 200, circuit.text)
        self.assertLess(circuit.json()["max_probability_difference"], 1e-12)

        aer = self.client.post(f"/api/experiments/{run_id}/aer", json={
            "interval_index": 1, "steps": 2, "shots": 128,
            "single_qubit_error": .001, "two_qubit_error": .01,
            "readout_error": .02, "kind": "c3", "index": 0})
        self.assertEqual(aer.status_code, 200, aer.text)
        self.assertEqual(aer.json()["metadata"]["shots"], 128)
        self.assertEqual(int(service.store.load(run_id)[2]["aer_counts"].sum()), 128)

        convergence = self.client.post(f"/api/experiments/{run_id}/convergence", json={})
        self.assertEqual(convergence.status_code, 200, convergence.text)
        self.assertIn("psa_independent_seed", convergence.json())
        self.assertEqual(self.client.get(f"/api/experiments/{run_id}").status_code, 200)
        manifest = self.client.get(f"/api/experiments/{run_id}/manifest").json()
        self.assertIn("app/backend/service.py", manifest["source_sha256"])
        self.assertEqual((Path(self.temp.name) / run_id / "current").read_text(), "0004")

    def test_invalid_config_and_missing_run(self):
        bad = self.client.post("/api/experiments", json={"config": {
            "n": 4, "flavors": [0, 0, 1, 1], "g_values": [[0, 1], [1, 0]]}})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.client.get("/api/experiments/invalid").status_code, 404)

    def test_background_job_reports_real_stages(self):
        request = {"config": {"n": 5, "mu": 1, "theta": .2,
                              "omega_values": [.8, .9, 1, 1.1, 1.2],
                              "g_values": [[0 if i == j else 1 for j in range(5)] for i in range(5)],
                              "t_max": 2, "points": 21, "flavors": [0, 0, 1, 1, 0], "seed": 3},
                   "trajectories": 64, "substeps": 2}
        started = self.client.post("/api/jobs/classical", json=request)
        self.assertEqual(started.status_code, 202, started.text)
        job_id = started.json()["job_id"]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            job = self.client.get(f"/api/jobs/{job_id}").json()
            if job["status"] in ("completed", "failed"):
                break
            time.sleep(.02)
        self.assertEqual(job["status"], "completed", job)
        stages = {event["stage"] for event in job["events"]}
        self.assertTrue({"config", "exact", "mean", "psa", "quality", "persist"} <= stages)
        self.assertEqual(self.client.get(f"/api/experiments/{job['run_id']}").json()["config"]["n"], 5)
        started_quantum = self.client.post(f"/api/jobs/{job['run_id']}/quantum", json={
            "steps": 2, "shots": 128, "readout_error": .02})
        self.assertEqual(started_quantum.status_code, 202, started_quantum.text)
        quantum_id = started_quantum.json()["job_id"]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            quantum_job = self.client.get(f"/api/jobs/{quantum_id}").json()
            if quantum_job["status"] in ("completed", "failed"):
                break
            time.sleep(.02)
        self.assertEqual(quantum_job["status"], "completed", quantum_job)
        self.assertIn("quantum", {event["stage"] for event in quantum_job["events"]})
        self.assertEqual(quantum_job["run_id"], job["run_id"])
        self.assertEqual(self.client.get(f"/api/experiments/{job['run_id']}").json()["quantum"]["options"]["shots"], 128)


if __name__ == "__main__":
    unittest.main()
