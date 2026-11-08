"""Controles físicos e estatísticos da extensão exploratória v3."""
import sys
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_correlation_search import config, complete_psa
from run_correlation_noise import analyze, c3, marginal, readout_matrix, response
import run_correlation_hardware as hardware
from run_correlation_search import digest
from neutrinos.sim import classical_exact, observable_from_counts


class CorrelationCampaignTests(unittest.TestCase):
    def test_complete_initial_ensemble_remains_uncorrelated_without_interaction(self):
        cfg = replace(config(4, 0., 'alternating', 'two_beam'), t_max=1., points=21)
        actual = complete_psa(cfg, 4, batch_size=37)
        exact = classical_exact(cfg)
        np.testing.assert_allclose(actual.pe, exact.pe, atol=1e-9)
        np.testing.assert_allclose(actual.c2, 0, atol=1e-12)
        np.testing.assert_allclose(actual.c3, 0, atol=1e-12)

    def test_marginal_keeps_logical_bit_order_and_complete_cumulant(self):
        counts = np.random.default_rng(5).multinomial(10000, np.ones(256) / 256)
        indices = (1, 4, 7)
        probabilities = marginal(counts / counts.sum(), indices)
        self.assertAlmostEqual(float(c3(probabilities)), observable_from_counts(counts, 'c3', indices), places=14)

    def test_asymmetric_independent_readout_inverse_recovers_nonzero_cumulant(self):
        p = np.zeros(8); p[0] = .7; p[-1] = .3
        single = np.array([[.9, .2], [.1, .8]])
        matrix = np.kron(single, np.kron(single, single))
        estimated = response(matrix[:, 0], matrix[:, -1])[0]
        np.testing.assert_allclose(estimated, matrix, atol=1e-14)
        corrected = np.linalg.solve(estimated, matrix @ p)
        self.assertAlmostEqual(float(c3(corrected)), float(c3(p)), places=13)
        self.assertGreater(abs(float(c3(matrix @ p)) - float(c3(p))), .01)

    def test_tiny_psa_error_does_not_make_a_biased_circuit_superior(self):
        zzz = np.prod(1 - 2 * ((np.arange(8)[:, None] >> np.arange(3)) & 1), axis=1)
        probabilities = (1 - .00365 * zzz) / 8
        result = analyze(probabilities, .00005, -.00004, 1e-5, 0., 42, repetitions=500)
        self.assertFalse(result['methods']['raw']['better_than_psa_pointwise'])
        self.assertGreater(result['methods']['raw']['D_ci95'][1], 0)

    def test_hardware_submission_requires_explicit_flag_before_connecting(self):
        with patch.object(hardware.ibm_runtime, '_service') as service:
            with self.assertRaisesRegex(ValueError, 'allow-hardware'):
                hardware.submit(Path('/nonexistent'), False)
            service.assert_not_called()

    def test_ambiguous_submission_cannot_duplicate_a_remote_job(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp); folder = output/'hardware'; folder.mkdir()
            plan = folder/'plan.json'; plan.write_text(json.dumps({'jobs': [{}]}))
            (folder/'collection.json').write_text(json.dumps({'plan_sha256': digest(plan),
                'jobs': [{'status': 'submission_uncertain', 'job_id': None}]}))
            with patch.object(hardware.ibm_runtime, '_service') as service:
                with self.assertRaisesRegex(ValueError, 'ambígua'):
                    hardware.submit(output, True)
                service.assert_not_called()


if __name__ == '__main__':
    unittest.main()
