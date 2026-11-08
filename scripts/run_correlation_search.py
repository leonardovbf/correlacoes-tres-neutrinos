#!/usr/bin/env python3
"""Busca exploratória v3 de cumulantes; nunca envia jobs IBM."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from app.backend.audit import atomic_json
from neutrinos.sim import (ExperimentConfig, MomentSeries, _evolve_spins,
    _moments_from_probabilities, classical_exact, trotter_probabilities)
from neutrinos.qiskit_backend import first_interval_probabilities
from neutrinos.study_analysis import metrics

DESIGN = ROOT / 'configs/protocols/correlacoes_v3/design.json'
DEFAULT = ROOT / 'results/campaigns/20261107-correlacoes-v3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design():
    return {'schema_version': 1, 'status': 'exploratory_after_v1_v2',
        'sizes': [4, 6, 8], 'mu': [1., 3., 10.],
        'initial_states': ['domain', 'alternating'], 'geometries': ['uniform', 'two_beam'],
        'theta': .2, 'omega': 'linspace(0.7,1.3,N)',
        'two_beam': 'indices below N/2 parallel; remaining antiparallel; g normalized to mean off-diagonal 1',
        'psa': 'equal-weight enumeration of all 4**N initial sign configurations; aggregate moments before cumulants',
        'time_grid': {'end': 3., 'points': 61, 'rk4_substeps': 4},
        'candidate_window': [.5, 2.5], 'minimum_exact_amplitude': .02,
        'minimum_psa_absolute_error': .02,
        'candidate_within_case': 'maximize gap/(1+(mu*tau)**2); first flattened index breaks ties',
        'trotter_steps': [1, 2, 4, 6, 8, 12, 16], 'primary_trotter_limit': .001,
        'candidate_between_cases': 'maximize gap/(nonzero_pairs*minimum_steps); ties use case id',
        'selected_psa_validation': 'repeat complete time-grid enumeration with 8 RK4 substeps; max c3 difference <=1e-5',
        'qiskit_probability_limit': 1e-10,
        'interpretation': 'All searches and local pointwise intervals are exploratory. Lower error than PSA is not computational quantum advantage.',
        'noise_plan': {'p2': [0., .0001, .0003, .001, .003, .01],
            'p1': 'p2/10', 'readout': [0., .03], 'circuits': ['minimum_steps', 'twice_minimum_steps'],
            'total_shots_per_method': 81920, 'mitigated_signal': 61440,
            'calibration_each': 10240, 'bootstrap_repetitions': 2000,
            'bootstrap': 'stationary multinomial for signal/calibration separately; deterministic PSA; preserve bit covariances',
            'success': 'upper CI95 of absolute-error difference D below zero; report numerical sensitivity and baseline C3=0'},
        'hardware_extension': {'maximum_jobs': 10, 'shots_per_job': 4096,
            'sizes': [6, 8], 'gate_twirling': True,
            'condition': 'local convergence and Qiskit pass; predicted advantage at p2=.001 and readout=.03; <=500 two-qubit gates, depth<=3000',
            'role': 'exploratory pilot; full counts measure all trios; five blocks per size; no claim of global superiority'},
        'separate_existing_confirmation': 'v2 selected N4 circuit, 20 jobs/327680 shots; original decision preserved'}


def config(n, mu, initial, geometry):
    flavors = tuple([0] * (n // 2) + [1] * (n // 2)) if initial == 'domain' else tuple(i % 2 for i in range(n))
    g = np.ones((n, n)) - np.eye(n)
    if geometry == 'two_beam':
        groups = np.arange(n) < n // 2
        g = (groups[:, None] != groups[None, :]).astype(float)
        g *= n * (n - 1) / g.sum()
    return ExperimentConfig(n=n, mu=mu, flavors=flavors, t_max=3., points=61,
        theta=.2, omega_values=tuple(np.linspace(.7, 1.3, n)),
        g_values=tuple(map(tuple, g)), seed=110001)


def initial_support(cfg, start, stop):
    labels = np.arange(start, stop, dtype=np.uint64)
    signs = 2 * ((labels[:, None] >> np.arange(2 * cfg.n, dtype=np.uint64)) & 1).astype(float) - 1
    signs = signs.reshape(-1, cfg.n, 2)
    spins = np.empty((len(labels), cfg.n, 3))
    for i, direction in enumerate(cfg.initial_bloch):
        anchor = np.array([0., 0., 1.]) if abs(direction[2]) < .9 else np.array([1., 0., 0.])
        u = np.cross(anchor, direction); u /= np.linalg.norm(u)
        v = np.cross(direction, u)
        spins[:, i] = direction + signs[:, i, 0, None] * u + signs[:, i, 1, None] * v
    return spins


def complete_psa(cfg, substeps=4, batch_size=1024):
    total = 4 ** cfg.n
    moments = [np.zeros((cfg.points, k)) for k in (cfg.n, len(cfg.pair_index), len(cfg.trio_index))]
    max_length_error = 0.
    for start in range(0, total, batch_size):
        spins = initial_support(cfg, start, min(start + batch_size, total))
        evolved = _evolve_spins(cfg, spins, substeps)
        max_length_error = max(max_length_error, float(np.max(np.abs(np.sum(evolved * evolved, axis=-1) - 3))))
        z = evolved[..., 2]
        moments[0] += z.sum(axis=1) / total
        for dest, groups in zip(moments[1:], (cfg.pair_index, cfg.trio_index)):
            for offset in range(0, len(groups), 8):
                indices = groups[offset:offset + 8]
                values = np.prod(z[:, :, indices], axis=-1)
                dest[:, offset:offset + len(indices)] += values.sum(axis=1) / total
    return MomentSeries(cfg.times, *moments, cfg.pair_index, cfg.trio_index,
        'PSA full discrete support', {'support': total, 'substeps': substeps,
        'max_squared_spin_length_error': max_length_error})


def point_candidate(cfg, exact, psa):
    gap = np.abs(exact.c3 - psa.c3)
    eligible = ((cfg.times[:, None] >= .5) & (cfg.times[:, None] <= 2.5)
        & (np.abs(exact.c3) >= .02) & (gap >= .02))
    score = np.where(eligible, gap / (1 + (cfg.mu * cfg.times[:, None]) ** 2), -np.inf)
    if not np.isfinite(score).any():
        return None
    t, trio = np.unravel_index(np.argmax(score), score.shape)
    point = replace(cfg, points=2, t_max=float(cfg.times[t]))
    variants = []
    minimum = None
    for steps in design()['trotter_steps']:
        probabilities, norm = trotter_probabilities(point, steps)
        ideal = _moments_from_probabilities(point, probabilities, 'ideal', {})
        error = float(abs(ideal.c3[-1, trio] - exact.c3[t, trio]))
        variants.append({'steps': steps, 'primary_error': error,
            'all_trios_max_error': float(np.max(np.abs(ideal.c3[-1] - exact.c3[t]))),
            'max_norm_error': norm})
        if minimum is None and error <= .001:
            minimum = steps
    if minimum is None:
        return None
    pairs = int(np.count_nonzero(np.triu(cfg.g_matrix, 1)))
    return {'time_index': int(t), 'tau': float(cfg.times[t]), 'trio_index': int(trio),
        'trio': cfg.trio_index[trio].tolist(), 'exact': float(exact.c3[t, trio]),
        'psa': float(psa.c3[t, trio]), 'gap': float(gap[t, trio]),
        'minimum_steps': minimum, 'nonzero_pairs': pairs,
        'selection_score': float(gap[t, trio] / (pairs * minimum)), 'trotter': variants}


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    expected = design()
    if not DESIGN.exists() or json.loads(DESIGN.read_text()) != expected:
        raise ValueError('Defina e versione o desenho antes de executar')
    sources = [Path(__file__), ROOT/'src/neutrinos/sim.py',
        ROOT/'src/neutrinos/qiskit_backend.py', ROOT/'src/neutrinos/study_analysis.py', DESIGN]
    identity = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    meta = output/'manifest.json'
    if meta.exists():
        if json.loads(meta.read_text())['source_sha256'] != identity:
            raise ValueError('Fontes mudaram; use outro diretório de campanha')
    else:
        for path in sources:
            target = output/'sources'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
        atomic_json(meta, {'status': 'running', 'source_sha256': identity,
            'numpy': np.__version__, 'python': sys.version, 'design': expected})
    all_cases = []
    for n in expected['sizes']:
        for mu in expected['mu']:
            for state in expected['initial_states']:
                for geometry in expected['geometries']:
                    name = f'n{n}_mu{mu:g}_{state}_{geometry}'
                    path = output/f'{name}.json'
                    if path.exists():
                        case = json.loads(path.read_text())
                        if digest(output/case['moments_path']) != case['moments_sha256']:
                            raise ValueError('Momentos da campanha foram alterados')
                        all_cases.append(case); continue
                    cfg = config(n, mu, state, geometry)
                    begin = time.perf_counter(); exact = classical_exact(cfg)
                    exact_seconds = time.perf_counter() - begin
                    begin = time.perf_counter(); psa = complete_psa(cfg)
                    seconds = time.perf_counter() - begin
                    data_path = output/f'{name}.npz'
                    np.savez_compressed(data_path, times=cfg.times, pairs=cfg.pair_index, trios=cfg.trio_index,
                        **{f'{prefix}_{key}': getattr(series, key) for prefix, series in [('exact', exact), ('psa', psa)]
                            for key in ('m1', 'm2', 'm3', 'pe', 'c2', 'c3')})
                    case = {'id': name, 'n': n, 'mu': mu, 'initial_state': state, 'geometry': geometry,
                        'config': cfg.record(), 'exact_seconds': exact_seconds, 'psa_seconds': seconds,
                        'psa_diagnostics': psa.diagnostics, 'exact_diagnostics': exact.diagnostics,
                        'metrics': {key: metrics(getattr(exact, key), getattr(psa, key)) for key in ('pe', 'c2', 'c3')},
                        'moments_path': data_path.name, 'moments_sha256': digest(data_path),
                        'candidate': point_candidate(cfg, exact, psa)}
                    atomic_json(path, case); all_cases.append(case)
                    print(f'{name}: PSA {seconds:.1f}s; gap candidato {case["candidate"]["gap"] if case["candidate"] else None}', flush=True)
    selected = []
    for n in expected['sizes']:
        candidates = [c for c in all_cases if c['n'] == n and c['candidate']]
        winner = sorted(candidates, key=lambda c: (-c['candidate']['selection_score'], c['id']))[0]
        cfg = config(n, winner['mu'], winner['initial_state'], winner['geometry'])
        fine_path = output/f'{winner["id"]}_refined.npz'
        if not fine_path.exists():
            fine = complete_psa(cfg, 8)
            np.savez_compressed(fine_path, c3=fine.c3, m1=fine.m1, m2=fine.m2, m3=fine.m3)
        with np.load(output/winner['moments_path']) as coarse, np.load(fine_path) as fine:
            difference = float(np.max(np.abs(coarse['psa_c3'] - fine['c3'])))
            t, trio = winner['candidate']['time_index'], winner['candidate']['trio_index']
            fine_value = float(fine['c3'][t, trio])
        point = replace(cfg, points=2, t_max=winner['candidate']['tau'])
        steps = winner['candidate']['minimum_steps']
        _, qiskit = first_interval_probabilities(point, steps)
        probabilities, _ = trotter_probabilities(point, steps)
        qerror = float(np.max(np.abs(qiskit - probabilities[-1])))
        selected.append({**winner, 'refinement_max_c3': difference,
            'psa_refined_at_endpoint': fine_value, 'qiskit_probability_error': qerror,
            'validation_pass': difference <= 1e-5 and qerror <= 1e-10,
            'refined_moments_path': fine_path.name, 'refined_moments_sha256': digest(fine_path)})
        print(f'Selected N={n}: {winner["id"]}, tau={point.t_max}, steps={steps}, convergence={difference:g}', flush=True)
    result = {'status': 'completed' if all(c['validation_pass'] for c in selected) else 'failed_validation',
        'scientific_status': 'exploratory', 'cases': all_cases, 'selected': selected,
        'source_manifest_sha256': digest(meta), 'ibm_jobs_submitted': 0}
    atomic_json(output/'search.json', result)
    with (output/'search.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'n', 'mu', 'initial_state', 'geometry',
            'exact_seconds', 'psa_seconds', 'pe_rmse', 'c2_rmse', 'c3_rmse', 'r3'])
        writer.writeheader()
        for c in all_cases:
            writer.writerow({**{k: c[k] for k in writer.fieldnames[:7]},
                **{f'{k}_rmse': c['metrics'][k]['rmse'] for k in ('pe', 'c2', 'c3')},
                'r3': c['metrics']['c3']['normalized_rmse']})
    print(output/'search.json', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['define', 'run'])
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    if args.command == 'define':
        if DESIGN.exists() and json.loads(DESIGN.read_text()) != design():
            raise SystemExit('Não sobrescrever desenho existente; crie uma nova versão')
        atomic_json(DESIGN, design()); print(DESIGN)
    else:
        run(args.output.resolve())
