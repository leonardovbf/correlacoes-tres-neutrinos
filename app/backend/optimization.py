"""Continuação auditada após otimização equivalente do integrador RK4.

O estudo original permanece intacto. Fontes científicas/protocolos não relacionados
à otimização não podem mudar. A transição exige comparação contra o solver arquivado.
"""
from __future__ import annotations

import copy
import fcntl
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from neutrinos import sim
from . import audit, protocol, service, study

ALLOWED_CHANGES = {'src/neutrinos/sim.py', 'app/backend/optimization.py',
                   'scripts/run_study.py', 'app/backend/study.py'}
FIELDS = ('sample_z', 'bloch', 'm1', 'm2', 'm3', 'pe', 'c2', 'c3')
TOLERANCE = 1e-10


def _baseline(root, record):
    snapshot = (root / record['source_snapshot']).resolve()
    if not snapshot.is_relative_to((root / '_sources').resolve()):
        raise ValueError('Snapshot fora da pasta de fontes')
    source = snapshot / 'src/neutrinos/sim.py'
    expected = record['environment']['source_sha256']['src/neutrinos/sim.py']
    if audit.file_hash(source) != expected:
        raise ValueError('Solver original arquivado foi alterado')
    name = '_neutrino_archived_' + expected
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _changes(previous, current):
    if previous['dependencies'] != current['dependencies'] or previous['python'] != current['python']:
        raise ValueError('Esta transição não permite trocar Python/dependências')
    left, right = previous['source_sha256'], current['source_sha256']
    changed = sorted(k for k in left.keys() | right.keys() if left.get(k) != right.get(k))
    unexpected = set(changed) - ALLOWED_CHANGES
    if unexpected:
        raise ValueError('Mudanças fora da otimização: ' + ', '.join(sorted(unexpected)))
    return changed


def _case_configs():
    # Todas as células físicas oficiais (sementes não alteram a EDO por trajetória).
    unique = {}
    for spec in study.official_specs():
        for step in spec.steps:
            if step.action != 'classical':
                continue
            cfg = dict(step.request['config'])
            cfg['seed'] = 10001
            key = json.dumps({'config': cfg, 'substeps': step.request['substeps']}, sort_keys=True)
            # A comparação longa usa a resolução final. Resoluções intermediárias
            # também têm cobertura unitária independente contra a EDO original.
            if step.request['substeps'] not in (12, 20):
                continue
            unique[key] = {'config': cfg, 'trajectories': 64, 'substeps': step.request['substeps']}
    for perturbation in (0., 1e-12):
        cfg = {'n': 4, 'mu': 10., 'theta': .2, 't_max': 10., 'points': 201,
            'flavors': [0, 0, 1, 1], 'seed': 10001, 'omega_values': [.7, .9, 1.1, 1.3],
            'g_values': [[0,1+perturbation,.5,0],[1+perturbation,0,1.2,.4],[.5,1.2,0,.8],[0,.4,.8,0]],
            'b_values': [.6,.8,0.], 'initial_bloch_values': [[.6,0,.8],[0,.6,.8],[-.6,0,-.8],[0,-.6,-.8]]}
        unique[str(perturbation)] = {'config': cfg, 'trajectories':64, 'substeps':12}
    return list(unique.values())


def verify(root, original, destination, *, progress=print, benchmark=True):
    current = audit.environment()
    changed = _changes(original['environment'], current)
    baseline = _baseline(root, original)
    report = {'schema_version':1, 'purpose':'validação numérica de implementação; não é coleta oficial',
        'status':'running', 'started_utc':audit.utc_now(), 'finished_utc':None,
        'previous_fingerprint':original['environment']['fingerprint'],
        'current_fingerprint':current['fingerprint'], 'changed_sources':changed,
        'max_absolute_difference_limit':TOLERANCE, 'cases':[], 'benchmark':None,
        'protocol_parameters_changed':False}
    audit.atomic_json(destination, report)
    try:
        cases = _case_configs()
        if benchmark:
            cases.append({'config':{'n':8,'mu':10.,'theta':.2,'points':201,'t_max':10.,'seed':10001,
                'flavors':[0,0,0,0,1,1,1,1], 'omega_values':np.linspace(.7,1.3,8).tolist(),
                'g_values':(np.ones((8,8))-np.eye(8)).tolist()}, 'trajectories':4096,'substeps':12,
                'benchmark':True})
        for i, case in enumerate(cases):
            progress(f'Equivalência RK4 {i+1}/{len(cases)}: N={case["config"]["n"]}, μ={case["config"]["mu"]}, M={case["trajectories"]}')
            report['current_case']={'index':i+1,'request':case,'started_utc':audit.utc_now()}
            audit.atomic_json(destination,report)
            outputs, durations = [], []
            for implementation in (baseline, sim):
                config = implementation.ExperimentConfig.from_dict(case['config'])
                started = time.perf_counter()
                psa = implementation.phase_space(config, case['trajectories'], case['substeps'])
                mean = implementation.mean_field(config, case['substeps'])
                durations.append(time.perf_counter()-started)
                outputs.append((psa, mean))
            differences = {}
            for label, pair in (('psa',(outputs[0][0],outputs[1][0])), ('mean',(outputs[0][1],outputs[1][1]))):
                for field in FIELDS:
                    left, right = (getattr(value,field) for value in pair)
                    if left is not None:
                        if left.shape != right.shape or not np.isfinite(right).all():
                            raise ValueError('Solver otimizado devolveu dimensões/valores inválidos')
                        differences[f'{label}_{field}'] = float(np.max(np.abs(left-right))) if left.size else 0.
            result = {**case, 'baseline_seconds':durations[0], 'optimized_seconds':durations[1],
                'speedup':durations[0]/durations[1], 'max_absolute_differences':differences,
                'started_utc':report['current_case']['started_utc'],'finished_utc':audit.utc_now(),
                'pass':all(value<=TOLERANCE for value in differences.values())}
            report['cases'].append(result)
            if case.get('benchmark'):
                report['benchmark'] = result
            audit.atomic_json(destination, report)
            if not result['pass']:
                raise ValueError('Equivalência numérica reprovada; estudo original preservado')
        if audit.environment()['fingerprint'] != current['fingerprint']:
            raise ValueError('Fontes mudaram durante a verificação')
        report['status']='passed'
    except BaseException as exc:
        report['status']='failed'
        report['error']=audit.safe_error(exc)
        raise
    finally:
        report['finished_utc']=audit.utc_now()
        audit.atomic_json(destination,report)
    return report


def prepare_continuation(path, *, progress=print):
    root = service.store.root.resolve()
    path = path.resolve()
    if path.parent.parent != root/'studies' or path.name!='study.json':
        raise ValueError('Use o mesmo --output do estudo original')
    with (path.parent/'.lock').open('a') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('O estudo está ativo; espere a fase terminar antes da otimização') from exc
        original = json.loads(path.read_text())
        if original['status']!='awaiting_next_phase':
            raise ValueError('A continuação deve começar entre fases concluídas, sem coleta ativa ou controle reprovado')
        if any(p['status'] not in ('pending','completed') for p in original['phases']):
            raise ValueError('Existe uma fase incompleta; finalize-a no snapshot original')
        snapshot = audit.environment()
        _changes(original['environment'],snapshot)
        specs = study.smoke_specs() if original['profile']=='software-smoke' else study.official_specs(original['extension'])
        for spec,phase in zip(specs,original['phases'],strict=True):
            if phase['name'] != spec.name:
                raise ValueError('Ordem dos protocolos alterada')
            if phase['status']!='completed':
                continue
            previous = json.loads(Path(phase['protocol_record']).read_text())
            saved = protocol.read_protocol(Path(phase['protocol_record']).parent/'protocol.json')
            if saved != spec:
                raise ValueError('Protocolo físico alterado')
            for step in previous['steps']:
                protocol.verify_artifacts(root,audit.load_execution(root,step['execution_id']))
            for artifact in phase['artifacts']:
                if audit.file_hash(path.parent/artifact['path']) != artifact['sha256']:
                    raise ValueError('Relatório/figura original alterado')
        destination = root/'studies'/audit.new_id()
        destination.mkdir(parents=True)
        verification = destination/'optimization_verification.json'
        report = verify(root,original,verification,progress=progress)
        if report['current_fingerprint'] != snapshot['fingerprint']:
            raise ValueError('Ambiente mudou durante a preparação')
        record = copy.deepcopy(original)
        for phase in record['phases']:
            for artifact in phase.get('artifacts',[]):
                target = destination/artifact['path']
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Relatório fora da pasta do estudo')
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path.parent/artifact['path'],target)
                if audit.file_hash(target)!=artifact['sha256']:
                    raise ValueError('Relatório mudou durante a cópia')
        record.update(started_utc=audit.utc_now(),finished_utc=None,process_id=None,error=None,
            environment=snapshot,source_snapshot=audit.archive_environment(root,snapshot),
            continuation={'kind':'equivalent_solver_optimization','parent_record':str(path),
                'parent_record_sha256':audit.file_hash(path),'parent_environment':original['environment'],
                'verification':{'path':verification.name,'sha256':audit.file_hash(verification)},
                'reused_phases':[p['name'] for p in original['phases'] if p['status']=='completed']})
        output = destination/'study.json'
        audit.atomic_json(output,record)
        audit.atomic_json(root/'studies'/'LATEST.json',{'record_path':str(output),'profile':record['profile']})
        return {'record_path':str(output),'status':record['status'], 'next_phase':record['next_phase'],
                'reused_phases':record['continuation']['reused_phases'],
                'benchmark_speedup':report['benchmark']['speedup']}
