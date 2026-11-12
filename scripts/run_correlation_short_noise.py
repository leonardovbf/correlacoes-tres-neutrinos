#!/usr/bin/env python3
"""Emenda exploratória v3: trocar precisão ideal excessiva por circuito curto."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT), str(ROOT/'src')]
from run_correlation_search import DEFAULT, config, digest
from run_correlation_noise import analyze, c3, marginal
from app.backend.audit import atomic_json
from neutrinos.qiskit_backend import build_trotter_circuit
from neutrinos.sim import trotter_probabilities

AMENDMENT = ROOT/'configs/protocols/correlacoes_v3/emenda_circuitos_curtos.json'


def amendment():
    return {'status': 'exploratory_after_ideal_search_before_new_hardware',
        'reason': 'The strict 0.001 ideal tolerance selects 6/8-qubit circuits with many gates. Compare a shorter approximation with explicit ideal error.',
        'selection': 'smallest tested step count with primary ideal error <= min(0.02,0.1*PSA-exact gap)',
        'comparison': 'same selected physical point, exact reference, complete PSA and noise grid; original strict candidates preserved',
        'hardware_rule': 'choose among strict, double and short candidates minimizing deterministic noisy absolute error at p2=.001, readout=.03; require raw D upper CI95<0, distinguish nonzero C3, beat C3=0; at most500 2q gates and depth3000',
        'hardware_budget': 'same maximum ten jobs, five blocks of4096 shots for each of N6 and N8; no extra jobs added',
        'interpretation': 'tests superiority in precision over PSA and zero baseline; does not assert equivalence at0.01 or computational advantage'}


def run(output):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    if json.loads(AMENDMENT.read_text()) != amendment():
        raise ValueError('Emenda ausente ou alterada')
    search_path = output/'search.json'; search = json.loads(search_path.read_text())
    folder = output/'short_noise'; folder.mkdir(exist_ok=True)
    inputs = {'search_sha256': digest(search_path), 'amendment_sha256': digest(AMENDMENT),
        'script_sha256': digest(Path(__file__)), 'helpers_sha256': digest(ROOT/'scripts/run_correlation_noise.py'),
        'compilation_amendment_sha256': digest(ROOT/'configs/protocols/correlacoes_v3/emenda_compilacao.json')}
    manifest = folder/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()) != inputs:
        raise ValueError('Entradas alteradas; preserve a campanha anterior')
    atomic_json(manifest, inputs)
    rows = []
    for selected in search['selected']:
        n = selected['n']; point = selected['candidate']
        limit = min(.02, .1*point['gap'])
        variant = next(v for v in point['trotter'] if v['primary_error'] <= limit)
        steps = variant['steps']
        cfg = replace(config(n, selected['mu'], selected['initial_state'], selected['geometry']), points=2, t_max=point['tau'])
        circuit = build_trotter_circuit(cfg, cfg.t_max, steps)
        compiled = transpile(circuit, basis_gates=['rz','sx','x','cx'], optimization_level=1,
            approximation_degree=1.0, seed_transpiler=130001)
        compiled.save_density_matrix()
        ideal, _ = trotter_probabilities(cfg, steps)
        for level, p2 in enumerate([0., .0001, .0003, .001, .003, .01]):
            path = folder/f'n{n}_p2_{p2:g}.json'
            if path.exists():
                rows.extend(json.loads(path.read_text())['observations']); continue
            noise = NoiseModel()
            if p2:
                noise.add_all_qubit_quantum_error(depolarizing_error(p2/10,1), ['sx','x'])
                noise.add_all_qubit_quantum_error(depolarizing_error(p2,2), ['cx'])
            simulator = AerSimulator(method='density_matrix', noise_model=noise,
                basis_gates=['rz','sx','x','cx'], max_parallel_threads=2)
            density = simulator.run(compiled, shots=1).result().data(0)['density_matrix']
            p = np.real(np.diag(np.asarray(density)))
            if np.min(p)<-1e-10 or abs(p.sum()-1)>1e-9:
                raise ValueError('Matriz densidade inválida')
            p = np.maximum(p,0); p /= p.sum()
            if not p2 and np.max(np.abs(p-ideal[-1]))>1e-10:
                raise ValueError('Compilação curta falhou na equivalência ideal')
            trio_p = marginal(p, point['trio'])
            observations = []
            for readout in (0., .03):
                row = analyze(trio_p, point['exact'], selected['psa_refined_at_endpoint'],
                    selected['refinement_max_c3'], readout, 170000+n*100+level*2+int(readout>0))
                row.update(n=n, factor=0, steps=steps, p2=p2, p1=p2/10, tau=cfg.t_max,
                    mu=cfg.mu, trio=point['trio'], case_id=selected['id'],
                    cx_count=int(compiled.count_ops().get('cx',0)), depth=compiled.depth(),
                    ideal_error=variant['primary_error'], ideal_limit=limit)
                observations.append(row)
            atomic_json(path, {'expected_probabilities_all_qubits': p.tolist(), 'observations': observations})
            rows.extend(observations)
            print(f'short N{n}, steps{steps}, p2={p2:g}, C3={c3(trio_p):.6f}', flush=True)
    atomic_json(output/'short_noise.json', {'status':'completed','scientific_status':'exploratory_amendment',
        'source_manifest_sha256':digest(manifest),'observations':rows,'ibm_jobs_submitted':0})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['define','run'])
    parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args()
    if args.command=='define':
        if AMENDMENT.exists() and json.loads(AMENDMENT.read_text()) != amendment():
            raise SystemExit('Preserve a emenda anterior')
        atomic_json(AMENDMENT,amendment())
    else:
        run(args.output.resolve())
