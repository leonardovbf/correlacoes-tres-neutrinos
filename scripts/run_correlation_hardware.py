#!/usr/bin/env python3
"""Prepara/envia/coleta a triagem IBM v3 de 6/8 qubits, até 10 jobs.

Os QPY preparados são os circuitos enviados. Estados ambíguos de submissão
exigem reconciliação por tags; nunca são reenviados automaticamente.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT), str(ROOT/'src')]
from run_correlation_search import DEFAULT, config, digest
from run_correlation_noise import c3, marginal
from app.backend import ibm_runtime
from app.backend.audit import atomic_json, safe_error
from neutrinos.qiskit_backend import build_trotter_circuit


def now():
    return datetime.now(timezone.utc).isoformat()


def prepare(output, backend_name):
    from qiskit import qpy
    from qiskit.transpiler import generate_preset_pass_manager
    search = json.loads((output/'search.json').read_text())
    noise = json.loads((output/'noise.json').read_text())
    short_noise = json.loads((output/'short_noise.json').read_text())
    if any(r['status'] != 'completed' for r in (search, noise, short_noise)):
        raise ValueError('As etapas locais precisam estar concluídas e validadas')
    folder = output/'hardware'; folder.mkdir(exist_ok=True)
    if (folder/'plan.json').exists():
        raise ValueError('Plano já existe: preserve-o e use submit/collect')
    backend = ibm_runtime._service().backend(backend_name)
    if not backend.status().operational or getattr(backend.configuration(), 'simulator', False):
        raise ValueError('Backend físico não operacional')
    plan = {'schema_version': 1, 'status': 'prepared_not_submitted', 'created_utc': now(),
        'backend': backend_name, 'scientific_status': 'exploratory_hardware_pilot',
        'sources_sha256': {p.name: digest(p) for p in [output/'search.json', output/'noise.json', output/'short_noise.json', Path(__file__),
            ROOT/'configs/protocols/correlacoes_v3/emenda_circuitos_curtos.json',
            ROOT/'configs/protocols/correlacoes_v3/emenda_compilacao.json']},
        'maximum_jobs': 10, 'shots_per_job': 4096, 'gate_twirling': True,
        'num_randomizations': 32, 'shots_per_randomization': 128,
        'analysis_before_data': 'aggregate moments; deterministic PSA reference; resample independent jobs only, with stationary multinomial sensitivity; no computational advantage claim',
        'candidates': [], 'skipped': [], 'jobs': []}
    properties = backend.properties()
    atomic_json(folder/'backend_properties.json', json.loads(json.dumps(properties.to_dict(), default=str)))
    plan['backend_properties_sha256'] = digest(folder/'backend_properties.json')
    for selected in search['selected']:
        n = selected['n']
        if n not in (6, 8):
            continue
        eligible = [r for r in noise['observations'] + short_noise['observations'] if r['n'] == n
            and r['p2'] == .001 and r['readout_error'] == .03]
        modeled = min(eligible, key=lambda r: (abs(r['expected_observed_c3']-r['exact']),r['steps']))
        lo,hi = modeled['methods']['raw']['difference_exact_ci95']
        estimate_interval = [lo+modeled['exact'],hi+modeled['exact']]
        upper_absolute_error = max(abs(lo),abs(hi))
        baseline_resolved = upper_absolute_error < abs(modeled['exact']) and (estimate_interval[0]>0 or estimate_interval[1]<0)
        if not selected['validation_pass'] or not modeled['methods']['raw']['better_than_psa_pointwise'] or not baseline_resolved:
            plan['skipped'].append({'n': n, 'reason': 'local precision or modeled raw advantage gate failed'})
            continue
        point = selected['candidate']
        cfg = replace(config(n, selected['mu'], selected['initial_state'], selected['geometry']),
            points=2, t_max=point['tau'])
        circuit = build_trotter_circuit(cfg, cfg.t_max, modeled['steps'])
        circuit.measure_all()
        compiled = generate_preset_pass_manager(backend=backend, optimization_level=1,
            approximation_degree=1.0, seed_transpiler=150001).run(circuit)
        gate_count = sum(count for instruction, count in compiled.count_ops().items()
            if instruction in {'cx', 'cz', 'ecr', 'rzz', 'rxx', 'ryy'})
        if gate_count > 500 or compiled.depth() > 3000:
            plan['skipped'].append({'n': n, 'reason': 'compiled resource gate failed',
                'two_qubit_gates': gate_count, 'depth': compiled.depth()})
            continue
        binary = io.BytesIO(); qpy.dump(compiled, binary)
        path = folder/f'n{n}.qpy'; path.write_bytes(binary.getvalue())
        inputs = {k: getattr(cfg, k) for k in cfg.__dataclass_fields__}
        candidate = {'n': n, 'case_id': selected['id'], 'config': inputs,
            'steps': modeled['steps'], 'trio': point['trio'], 'exact': point['exact'],
            'psa': selected['psa_refined_at_endpoint'], 'psa_numerical_sensitivity': selected['refinement_max_c3'],
            'qpy_path': path.name, 'qpy_sha256': digest(path), 'two_qubit_gates': int(gate_count),
            'depth': int(compiled.depth()), 'physical_qubits': compiled.layout.final_index_layout(),
            'modeled_raw_D_ci95': modeled['methods']['raw']['D_ci95']}
        plan['candidates'].append(candidate)
        for block in range(5):
            plan['jobs'].append({'slot': f'correlacoes-v3-n{n}-b{block+1}', 'n': n,
                'block': block+1, 'status': 'planned', 'job_id': None})
    plan['planned_jobs'] = len(plan['jobs']); plan['total_shots'] = 4096 * len(plan['jobs'])
    atomic_json(folder/'plan.json', plan)
    atomic_json(folder/'collection.json', {'plan_sha256': digest(folder/'plan.json'),
        'status': 'prepared_not_submitted', 'jobs': plan['jobs']})
    print(json.dumps(plan, indent=2))


def submit(output, allow_hardware):
    from qiskit import qpy
    from qiskit_ibm_runtime.executor_sampler import Sampler
    if not allow_hardware:
        raise ValueError('Envio exige --allow-hardware e consome recursos IBM')
    folder = output/'hardware'
    plan = json.loads((folder/'plan.json').read_text())
    state = json.loads((folder/'collection.json').read_text())
    if state['plan_sha256'] != digest(folder/'plan.json') or len(plan['jobs']) > 10:
        raise ValueError('Plano alterado ou orçamento excedido')
    if any(j['status'] in ('submitting', 'submission_uncertain') for j in state['jobs']):
        raise ValueError('Submissão ambígua: reconciliar jobs por tags antes de retomar')
    client = ibm_runtime._service(); backend = client.backend(plan['backend'])
    for job_state in state['jobs']:
        if job_state['job_id']:
            continue
        candidate = next(c for c in plan['candidates'] if c['n'] == job_state['n'])
        path = folder/candidate['qpy_path']
        if digest(path) != candidate['qpy_sha256']:
            raise ValueError('Circuito QPY alterado')
        with path.open('rb') as stream:
            circuit = qpy.load(stream)[0]
        sampler = Sampler(mode=backend)
        sampler.options.twirling.enable_gates = True
        sampler.options.twirling.num_randomizations = 32
        sampler.options.twirling.shots_per_randomization = 128
        sampler.options.environment.job_tags = ['correlacoes-v3', job_state['slot']]
        job_state.update(status='submitting', started_utc=now())
        atomic_json(folder/'collection.json', state)
        try:
            job = sampler.run([circuit], shots=4096)
            job_state.update(job_id=job.job_id(), status='submitted', submitted_utc=now())
        except Exception as exc:
            job_state.update(status='submission_uncertain', error=safe_error(exc))
            atomic_json(folder/'collection.json', state)
            raise
        atomic_json(folder/'collection.json', state)
        print(f'{job_state["slot"]}: {job_state["job_id"]}', flush=True)
    state['status'] = 'submitted' if state['jobs'] else 'no_viable_candidates'
    atomic_json(folder/'collection.json', state)


def collect(output):
    folder = output/'hardware'
    plan = json.loads((folder/'plan.json').read_text())
    state = json.loads((folder/'collection.json').read_text())
    if state['plan_sha256'] != digest(folder/'plan.json'):
        raise ValueError('Plano alterado')
    client = ibm_runtime._service()
    grouped = {}
    for slot in state['jobs']:
        if not slot['job_id']:
            continue
        data_path = folder/f'{slot["slot"]}_counts.json'
        if data_path.exists():
            data = json.loads(data_path.read_text())
            if data['job_id'] != slot['job_id']:
                raise ValueError('Contagens com job incompatível')
        else:
            job = client.job(slot['job_id'])
            status = job.status(); slot['status'] = str(getattr(status, 'value', status)).upper()
            if slot['status'] != 'DONE':
                print(slot['slot'], slot['status'], flush=True); continue
            counts = np.zeros(1 << slot['n'], dtype=np.int64)
            for bits, count in job.result()[0].data.meas.get_counts().items():
                counts[int(bits.replace(' ', ''), 2)] = count
            if counts.sum() != 4096:
                raise ValueError('Orçamento de contagens inesperado')
            data = {'job_id': slot['job_id'], 'counts': counts.tolist(), 'collected_utc': now()}
            atomic_json(data_path, data)
        slot['status'] = 'DONE'; slot['counts_sha256'] = digest(data_path)
        candidate = next(c for c in plan['candidates'] if c['n'] == slot['n'])
        grouped.setdefault(slot['n'], []).append(marginal(np.asarray(data['counts']), candidate['trio']))
    state['last_collected_utc'] = now()
    state['status'] = 'completed' if state['jobs'] and all(j['status'] == 'DONE' for j in state['jobs']) else 'awaiting_jobs'
    atomic_json(folder/'collection.json', state)
    analysis = {'scientific_status': 'exploratory', 'status': state['status'], 'cases': []}
    for n, blocks in grouped.items():
        candidate = next(c for c in plan['candidates'] if c['n'] == n)
        counts = np.sum(blocks, axis=0)
        center = float(c3(counts / counts.sum()))
        rng = np.random.default_rng(160000+n)
        cluster = np.asarray([np.sum([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))], axis=0) for _ in range(4000)])
        shot = rng.multinomial(int(counts.sum()), counts / counts.sum(), size=4000)
        methods = {}
        for key, samples in [('independent_job_blocks', cluster), ('stationary_multinomial', shot)]:
            estimates = c3(samples / samples.sum(axis=-1, keepdims=True))
            advantage = np.abs(estimates-candidate['exact']) - abs(candidate['psa']-candidate['exact'])
            low, high = np.quantile(advantage, [.025, .975])
            numerical = candidate['psa_numerical_sensitivity']
            methods[key] = {'D_ci95': [float(low-numerical), float(high+numerical)],
                'estimate_ci95': np.quantile(estimates, [.025, .975]).tolist()}
        analysis['cases'].append({'n': n, 'complete_blocks': len(blocks), 'estimate': center,
            'exact': candidate['exact'], 'psa': candidate['psa'],
            'D': abs(center-candidate['exact'])-abs(candidate['psa']-candidate['exact']),
            'uncertainty_sensitivity': methods,
            'interpretation': 'pilot pointwise intervals; no global or computational quantum advantage claim'})
    atomic_json(folder/'analysis.json', analysis)
    print(json.dumps(analysis, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'submit', 'collect'])
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--backend', default='ibm_kingston')
    parser.add_argument('--allow-hardware', action='store_true')
    args = parser.parse_args(); output = args.output.resolve()
    if args.command == 'prepare':
        prepare(output, args.backend)
    elif args.command == 'submit':
        submit(output, args.allow_hardware)
    else:
        collect(output)
