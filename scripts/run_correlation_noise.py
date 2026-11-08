#!/usr/bin/env python3
"""Ruído e orçamento igual nos candidatos exploratórios v3; execução local."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT), str(ROOT / 'src')]
from run_correlation_search import DEFAULT, config, digest
from app.backend.audit import atomic_json
from neutrinos.qiskit_backend import build_trotter_circuit
from neutrinos.sim import trotter_probabilities

BITS = ((np.arange(8)[:, None] >> np.arange(3)) & 1)
Z = 1 - 2 * BITS
ZZ = Z[:, [0, 0, 1]] * Z[:, [1, 2, 2]]
ZZZ = np.prod(Z, axis=1)


def c3(probabilities):
    p = np.asarray(probabilities)
    m1, m2, m3 = p @ Z, p @ ZZ, p @ ZZZ
    return m3 - m1[..., 0] * m2[..., 2] - m1[..., 1] * m2[..., 1] - m1[..., 2] * m2[..., 0] + 2 * np.prod(m1, axis=-1)


def marginal(probabilities, indices):
    states = np.arange(len(probabilities))
    labels = sum(((states >> q) & 1) << k for k, q in enumerate(indices))
    return np.bincount(labels, weights=probabilities, minlength=8)


def response(zero, one):
    zero, one = np.atleast_2d(zero), np.atleast_2d(one)
    p0 = zero @ BITS / zero.sum(axis=-1, keepdims=True)
    p1 = one @ BITS / one.sum(axis=-1, keepdims=True)
    result = np.ones((len(zero), 8, 8))
    for q in range(3):
        prob_one = np.where(BITS[None, None, :, q] == 0, p0[:, q, None, None], p1[:, q, None, None])
        result *= np.where(BITS[None, :, None, q] == 1, prob_one, 1 - prob_one)
    return result


def readout_matrix(error):
    distance = np.sum(BITS[:, None] != BITS[None, :], axis=-1)
    return error ** distance * (1 - error) ** (3 - distance)


def analyze(probabilities, exact, psa, numerical_sensitivity, readout, seed, repetitions=2000):
    rng = np.random.default_rng(seed)
    matrix = readout_matrix(readout)
    observed = matrix @ probabilities
    counts = {'raw': rng.multinomial(81920, observed), 'signal': rng.multinomial(61440, observed),
        'zero': rng.multinomial(10240, matrix[:, 0]), 'one': rng.multinomial(10240, matrix[:, -1])}
    calibration = response(counts['zero'], counts['one'])
    corrected = np.linalg.solve(calibration, (counts['signal'] / 61440)[None, :, None])[0, :, 0]
    central = {'raw': float(c3(counts['raw'] / 81920)), 'mitigated': float(c3(corrected))}
    draws = {key: rng.multinomial(int(values.sum()), values / values.sum(), size=repetitions)
        for key, values in counts.items()}
    calibrations = response(draws['zero'], draws['one'])
    condition = float(np.max(np.linalg.cond(calibrations)))
    if condition > 10 or not np.isfinite(condition):
        return {'status': 'unresolved_calibration', 'max_condition': condition}
    mitigated = np.linalg.solve(calibrations, (draws['signal'] / 61440)[..., None])[..., 0]
    values = {'raw': c3(draws['raw'] / 81920), 'mitigated': c3(mitigated)}
    methods = {}
    baseline_error = abs(psa - exact)
    for key, v in values.items():
        delta = np.abs(v - exact) - baseline_error
        low, high = np.quantile(delta, [.025, .975])
        ci = [float(low - numerical_sensitivity), float(high + numerical_sensitivity)]
        diff_exact = np.quantile(v - exact, [.025, .975]).tolist()
        methods[key] = {'estimate': central[key], 'absolute_error': abs(central[key] - exact),
            'D': abs(central[key] - exact) - baseline_error, 'D_ci95': ci,
            'better_than_psa_pointwise': bool(ci[1] < 0), 'difference_exact_ci95': diff_exact,
            'equivalent_to_exact_pointwise': bool(diff_exact[0] >= -.01 and diff_exact[1] <= .01)}
    return {'status': 'analyzed', 'methods': methods, 'count_vectors_trio': {k: v.tolist() for k, v in counts.items()},
        'stationary_bootstrap_repetitions': repetitions, 'seed': seed,
        'budget_per_method': 81920, 'readout_error': readout,
        'expected_gate_c3': float(c3(probabilities)), 'expected_observed_c3': float(c3(observed)),
        'psa': psa, 'exact': exact, 'max_bootstrap_calibration_condition': condition}


def run(output):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    source = output/'search.json'
    search = json.loads(source.read_text())
    if search['status'] != 'completed':
        raise ValueError('Complete e valide a busca antes de simular ruído')
    folder = output/'noise'; folder.mkdir(exist_ok=True)
    inputs = {'search_sha256': digest(source), 'script_sha256': digest(Path(__file__)),
        'basis': ['rz', 'sx', 'x', 'cx'], 'optimization_level': 1,
        'compilation_amendment_sha256': digest(ROOT/'configs/protocols/correlacoes_v3/emenda_compilacao.json'),
        'seed_transpiler': 130001, 'model': 'generic depolarizing; no IBM calibration',
        'analysis': 'pointwise exploratory stationary multinomial; no global detection claim'}
    manifest = folder/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()) != inputs:
        raise ValueError('Entradas da análise de ruído mudaram; preserve resultados anteriores')
    atomic_json(manifest, inputs)
    rows = []
    for selected in search['selected']:
        n = selected['n']; endpoint = selected['candidate']
        cfg = replace(config(n, selected['mu'], selected['initial_state'], selected['geometry']),
            points=2, t_max=endpoint['tau'])
        for factor in (1, 2):
            steps = endpoint['minimum_steps'] * factor
            circuit = build_trotter_circuit(cfg, cfg.t_max, steps)
            compiled = transpile(circuit, basis_gates=inputs['basis'], optimization_level=1,
                approximation_degree=1.0, seed_transpiler=130001)
            compiled.save_density_matrix()
            ideal, _ = trotter_probabilities(cfg, steps)
            for level, p2 in enumerate([0., .0001, .0003, .001, .003, .01]):
                key = f'n{n}_factor{factor}_p2_{p2:g}'
                path = folder/f'{key}.json'
                if path.exists():
                    rows.extend(json.loads(path.read_text())['observations']); continue
                noise = NoiseModel()
                if p2:
                    noise.add_all_qubit_quantum_error(depolarizing_error(p2 / 10, 1), ['sx', 'x'])
                    noise.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ['cx'])
                simulator = AerSimulator(method='density_matrix', noise_model=noise,
                    basis_gates=inputs['basis'], max_parallel_threads=2)
                begin = time.perf_counter()
                density = simulator.run(compiled, shots=1).result().data(0)['density_matrix']
                probabilities = np.real(np.diag(np.asarray(density)))
                if np.min(probabilities) < -1e-10 or abs(probabilities.sum() - 1) > 1e-9:
                    raise ValueError('Matriz densidade inválida')
                probabilities = np.maximum(probabilities, 0); probabilities /= probabilities.sum()
                if not p2 and np.max(np.abs(probabilities - ideal[-1])) > 1e-10:
                    raise ValueError('Aer sem ruído diverge da evolução ideal')
                trio_probability = marginal(probabilities, endpoint['trio'])
                observations = []
                for readout in (0., .03):
                    observation = analyze(trio_probability, endpoint['exact'], selected['psa_refined_at_endpoint'],
                        selected['refinement_max_c3'], readout,
                        seed=140000 + n * 1000 + factor * 100 + level * 2 + int(readout > 0))
                    observation.update(n=n, steps=steps, factor=factor, p2=p2, p1=p2 / 10,
                        tau=cfg.t_max, mu=cfg.mu, trio=endpoint['trio'], case_id=selected['id'],
                        cx_count=int(compiled.count_ops().get('cx', 0)), depth=int(compiled.depth()))
                    observations.append(observation)
                atomic_json(path, {'expected_probabilities_all_qubits': probabilities.tolist(),
                    'observations': observations, 'seconds': time.perf_counter() - begin})
                rows.extend(observations)
                print(f'{key}: depth={compiled.depth()}, cx={compiled.count_ops().get("cx", 0)}, C3={c3(trio_probability):.5f}', flush=True)
    atomic_json(output/'noise.json', {'status': 'completed', 'scientific_status': 'exploratory',
        'source_manifest_sha256': digest(manifest), 'observations': rows, 'ibm_jobs_submitted': 0})
    with (output/'noise.csv').open('w') as stream:
        names = ['n', 'mu', 'tau', 'steps', 'factor', 'p2', 'readout_error', 'cx_count', 'method',
            'exact', 'psa', 'estimate', 'absolute_error', 'D', 'D_low', 'D_high', 'better', 'equivalent']
        writer = csv.DictWriter(stream, fieldnames=names); writer.writeheader()
        for row in rows:
            for method, values in row.get('methods', {}).items():
                writer.writerow({**{k: row[k] for k in names[:8]}, 'method': method,
                    'exact': row['exact'], 'psa': row['psa'],
                    **{k: values[k] for k in ('estimate', 'absolute_error', 'D')},
                    'D_low': values['D_ci95'][0], 'D_high': values['D_ci95'][1],
                    'better': values['better_than_psa_pointwise'], 'equivalent': values['equivalent_to_exact_pointwise']})
    print(output/'noise.json', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    run(parser.parse_args().output.resolve())
