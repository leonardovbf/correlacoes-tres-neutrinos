"""Valida o desenho experimental versionado, sem executar as grades científicas."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from app.backend.protocol import ProtocolSpec


ROOT = Path(__file__).resolve().parents[1]


class StudyProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("study_design", ROOT / "scripts/define_article_protocols.py")
        cls.generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.generator)
        cls.files = cls.generator.design_files()
        cls.catalog = cls.files["configs/estudos/artigo_v1.json"]

    def test_versioned_files_match_design_and_all_executable_protocols_validate(self):
        executable = 0
        for name, expected in self.files.items():
            actual = json.loads((ROOT / name).read_text())
            self.assertEqual(actual, expected, name)
            if "steps" in actual:
                ProtocolSpec.model_validate(actual)
                executable += 1
        self.assertEqual(executable, 11)

    def test_primary_grid_contains_all_cases_and_uses_independent_official_seeds(self):
        protocol = self.files["configs/protocols/artigo_v1/03_classica_principal.json"]
        cells = {}
        for step in protocol["steps"]:
            request = step["request"]
            config = request["config"]
            cells.setdefault((config["n"], config["mu"]), set()).add(config["seed"])
            self.assertEqual(request["trajectories"], 4096)
            self.assertEqual(request["substeps"], 12)
            self.assertAlmostEqual(sum(config["omega_values"]) / config["n"], 1.)
        self.assertEqual(set(cells), {(n, mu) for n in (4, 6, 8) for mu in (.1, .3, 1., 3., 10.)})
        for seeds in cells.values():
            self.assertEqual(seeds, set(range(10001, 10021)))
            self.assertTrue(seeds.isdisjoint(range(1, 6)))

    def test_noise_grid_obeys_depth_limit_and_contains_predeclared_primary_endpoint(self):
        spec = self.files["configs/protocols/artigo_v1/06_ruido.json"]
        refs = {step["id"]: step["request"]["config"] for step in spec["steps"] if step["action"] == "classical"}
        primary = self.catalog["analysis"]["h2_primary_endpoint"]
        primary_repetitions = 0
        for step in spec["steps"]:
            if step["action"] != "aer":
                continue
            request, config = step["request"], refs[step["run_from"]]
            self.assertLess(request["interval_index"], config["points"])
            self.assertLessEqual(request["interval_index"] * request["steps"], 120)
            self.assertEqual(config["n"], 4)
            if (config["mu"] == primary["mu"] and config["t_max"] == primary["tau"]
                    and request["shots"] == primary["shots_per_repetition_total"]
                    and request["readout_error"] == .03):
                primary_repetitions += 1
        self.assertEqual(primary_repetitions, primary["repetitions"])
        mitigation = self.files["configs/protocols/artigo_v1/especificacoes/mitigacao.json"]
        budget = mitigation["budget"]
        self.assertEqual(budget["mitigated_signal_fraction"] + 2 * budget["calibration_shots_fraction_each_state"],
                         budget["unmitigated_signal_fraction"])
        self.assertEqual(mitigation["execution_status"], "executavel-em-07_mitigacao")


if __name__ == "__main__":
    unittest.main()
