"""Verifica os controles físicos e a separação das novas amostras."""

import importlib.util
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from app.backend import audit, ibm_runtime, protocol, service
from app.backend.storage import RunStore

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "short_circuit_experiments", ROOT / "scripts" / "prepare_short_circuit_experiments.py")
short = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(short)


class ShortCircuitTests(unittest.TestCase):
    def test_ideal_precision_has_distinct_scope_for_two_and_six_steps(self):
        report = short.ideal_preflight()
        self.assertEqual(report["status"], "passed")
        two = report["cases"]["principal_2passos"]
        six = report["cases"]["todos_6passos"]
        self.assertLess(two["primary_c3_error"], .001)
        self.assertGreater(two["all_trios_max_c3_error"], .001)
        self.assertLess(six["all_trios_max_c3_error"], .001)
        self.assertLess(max(two["qiskit_probability_error"], six["qiskit_probability_error"]), 1e-10)

    def test_local_screen_and_confirmation_use_separate_seeds(self):
        design = short.design()
        local = set(design["local"]["psa_seeds"])
        screen = set(design["hardware_screen"]["seeds"])
        confirm = set(design["confirmation"]["seeds"])
        self.assertFalse(local & screen or local & confirm or screen & confirm)
        self.assertEqual(design["hardware_screen"]["planned_jobs"], 20)
        self.assertEqual(design["confirmation"]["planned_jobs"], 20)
        self.assertEqual(len(short.local_protocol().steps), 82)

    def test_hardware_screen_collects_five_independent_blocks_per_arm_offline(self):
        steps = []
        for candidate, settings in short.CANDIDATES.items():
            for seed in short.SCREEN_SEEDS:
                parent = f"{candidate}_s{seed}"
                steps.extend([
                    {"id": parent, "action": "classical", "request": {
                        "config": short.config(seed), "trajectories": 16, "substeps": 1}},
                    {"id": parent + "_ideal", "action": "quantum", "run_from": parent,
                     "request": {"steps": settings["steps"], "shots": 32, "readout_error": 0}},
                ])
                for arm, twirling in (("plain", False), ("twirled", True)):
                    steps.append({"id": parent + "_" + arm, "action": "hardware",
                                  "run_from": parent, "request": {"backend": "fake_backend",
                                      "interval_index": 1, "steps": settings["steps"],
                                      "shots": 32, "kind": "c3", "index": 0,
                                      "role": "raw", "optimization_level": 3,
                                      "gate_twirling": twirling}})
        spec = protocol.ProtocolSpec(name="T10-circuitos-curtos-IBM-triagem-v2", steps=steps)
        with tempfile.TemporaryDirectory() as temp:
            old_store = service.store
            service.store = RunStore(Path(temp))
            sequence = iter(range(20))
            def fake_submit(_config, _request):
                return {"job_id": f"offline-{next(sequence)}", "backend": "fake_backend",
                        "transpiled_depth": 10, "two_qubit_gates": 2}
            counts = np.zeros(16, dtype=np.int64)
            counts[0] = 32
            try:
                with patch.object(ibm_runtime, "submit", side_effect=fake_submit), patch.object(
                        ibm_runtime, "fetch", return_value=("DONE", counts)), patch.object(
                        ibm_runtime, "shared_session", return_value=nullcontext()):
                    record = protocol.run_protocol(spec, allow_hardware=True)
                    report = short.collect_hardware(Path(record["record_path"]), Path(temp))
                self.assertEqual(report["status"], "analyzed")
                self.assertEqual(len(report["arms"]), 4)
                self.assertEqual({arm["blocks"] for arm in report["arms"].values()}, {5})
                self.assertEqual({arm["shots"] for arm in report["arms"].values()}, {160})
                self.assertIn(report["selected_for_confirmation"], report["arms"])
                from qiskit_ibm_runtime.fake_provider import FakeKingston
                folder = Path(temp) / "short-circuit-preparations" / "offline"
                spec_path = folder / "hardware_screen_protocol.json"
                audit.atomic_json(spec_path, spec.model_dump(mode="json"))
                preview = folder / "preview.qpy"
                preview.write_bytes(b"offline-preview")
                audit.atomic_json(folder / "plan.json", {
                    "protocol_sha256": audit.file_hash(spec_path),
                    "backend": "fake_kingston",
                    "previews": {name: {"initial_layout": [0, 1, 2, 3],
                                         "qpy_file": preview.name,
                                         "qpy_sha256": audit.file_hash(preview)}
                                 for name in short.CANDIDATES},
                })
                cloud = Mock()
                cloud.backend.return_value = FakeKingston()
                with patch.object(ibm_runtime, "_service", return_value=cloud):
                    prepared = short.prepare_confirmation(Path(record["record_path"]), Path(temp))
                self.assertEqual(prepared["status"], "prepared_not_submitted")
                confirm = protocol.read_protocol(Path(prepared["protocol_path"]))
                self.assertEqual(sum(step.action == "hardware" for step in confirm.steps), 20)
                self.assertEqual({step.request["shots"] for step in confirm.steps
                                  if step.action == "hardware"}, {16384})
            finally:
                service.store = old_store


if __name__ == "__main__":
    unittest.main()
