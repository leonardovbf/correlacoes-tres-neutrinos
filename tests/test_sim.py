import unittest

import numpy as np

from neutrinos import ExperimentConfig, bootstrap_interval, classical_exact, mean_field, observable_from_counts, phase_space, quantum_trotter, summarize_errors
from neutrinos.sim import hamiltonian_sparse


class PhysicalConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.config = ExperimentConfig(points=21, t_max=3.0)

    def test_hamiltonian_is_hermitian_and_initial_product_has_no_connected_z_moments(self):
        h = hamiltonian_sparse(self.config)
        difference = h - h.getH()
        self.assertLess(np.max(np.abs(difference.data)) if difference.nnz else 0.0, 1e-12)
        exact = classical_exact(self.config)
        self.assertLess(exact.diagnostics["max_norm_error"], 1e-10)
        self.assertTrue(np.allclose(exact.c2[0], 0, atol=1e-12))
        self.assertTrue(np.allclose(exact.c3[0], 0, atol=1e-12))

    def test_without_interaction_exact_and_mean_field_agree(self):
        config = ExperimentConfig(mu=0, points=21, t_max=3.0)
        error = summarize_errors(classical_exact(config), mean_field(config, substeps=4))
        self.assertLess(error["pe"]["max_abs"], 1e-6)
        self.assertLess(error["c2"]["max_abs"], 1e-10)
        self.assertLess(error["c3"]["max_abs"], 1e-10)

    def test_psa_matches_product_state_z_moments_initially(self):
        exact = classical_exact(self.config)
        psa = phase_space(self.config, trajectories=64)
        for field in ("m1", "m2", "m3"):
            self.assertTrue(np.allclose(getattr(exact, field)[0], getattr(psa, field)[0], atol=1e-12))

    def test_symmetric_trotter_converges_to_exact(self):
        config = ExperimentConfig(mu=3, points=21, t_max=4)
        exact = classical_exact(config)
        coarse, _ = quantum_trotter(config, steps_per_interval=1, shots=128)
        fine, _ = quantum_trotter(config, steps_per_interval=4, shots=128)
        coarse_error = summarize_errors(exact, coarse)["c3"]["rmse"]
        fine_error = summarize_errors(exact, fine)["c3"]["rmse"]
        self.assertLess(fine_error, coarse_error / 4)

    def test_qiskit_circuit_matches_gate_emulator_for_one_interval(self):
        try:
            from neutrinos.qiskit_backend import first_interval_probabilities
        except ImportError:
            self.skipTest("Qiskit não instalado")
        from neutrinos.sim import _symmetric_trotter_step, initial_state

        config = ExperimentConfig(points=11, t_max=1.0)
        steps = 2
        _, qiskit_probabilities = first_interval_probabilities(config, steps)
        state = initial_state(config)
        for _ in range(steps):
            _symmetric_trotter_step(state, config, (config.times[1] - config.times[0]) / steps)
        self.assertTrue(np.allclose(qiskit_probabilities, np.abs(state) ** 2, atol=1e-12))

    def test_bootstrap_uses_complete_trajectories_and_measurements(self):
        psa = phase_space(self.config, trajectories=64)
        _, measured = quantum_trotter(self.config, steps_per_interval=2, shots=256)
        for series in (psa, measured):
            lower, upper = bootstrap_interval(series, "c3", 0, repetitions=30, seed=9)
            self.assertEqual(lower.shape, (self.config.points,))
            self.assertTrue(np.all(np.isfinite(lower)))
            self.assertTrue(np.all(lower <= upper + 1e-12))
            self.assertLess(abs(lower[0]), 1e-12)
            self.assertLess(abs(upper[0]), 1e-12)

    def test_custom_couplings_and_field_match_qiskit(self):
        from neutrinos.qiskit_backend import first_interval_probabilities
        from neutrinos.sim import _symmetric_trotter_step, initial_state

        config = ExperimentConfig.from_dict({
            "n": 4, "flavors": [0, 1, 0, 1], "points": 11, "t_max": 1.0,
            "omega_values": [0.7, 1.1, 0.8, 1.4],
            "b_values": [0.6, 0.8, 0.0],
            "g_values": [[0, 1, .5, 0], [1, 0, 1.2, .4], [.5, 1.2, 0, .8], [0, .4, .8, 0]],
            "initial_bloch_values": [[.6, 0, .8], [0, .6, .8], [-.6, 0, -.8], [0, -.6, -.8]],
        })
        h = hamiltonian_sparse(config)
        self.assertLess(np.max(np.abs((h - h.getH()).data)) if (h - h.getH()).nnz else 0, 1e-12)
        _, qiskit_probabilities = first_interval_probabilities(config, 2)
        state = initial_state(config)
        for _ in range(2):
            _symmetric_trotter_step(state, config, .05)
        self.assertTrue(np.allclose(qiskit_probabilities, np.abs(state) ** 2, atol=1e-12))
        free = ExperimentConfig.from_dict({**{
            "n": 4, "flavors": [0, 1, 0, 1], "points": 11, "t_max": 1.0,
            "initial_bloch_values": [[.6, 0, .8], [0, .6, .8], [-.6, 0, -.8], [0, -.6, -.8]],
        }, "mu": 0})
        self.assertLess(summarize_errors(classical_exact(free), mean_field(free))["pe"]["max_abs"], 1e-6)

    def test_aer_gate_noise_returns_traceable_counts(self):
        from neutrinos.qiskit_backend import simulate_gate_noise

        config = ExperimentConfig(points=11, t_max=1.0)
        counts, metadata = simulate_gate_noise(config, 1, 1, 128, .001, .01, .02)
        self.assertEqual(int(counts.sum()), 128)
        self.assertGreater(metadata["cx_count"], 0)
        self.assertTrue(np.isfinite(observable_from_counts(counts, "c3", (0, 1, 2))))


if __name__ == "__main__":
    unittest.main()
