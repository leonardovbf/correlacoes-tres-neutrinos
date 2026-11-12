#!/usr/bin/env python3
"""Arquiva entradas de jobs IBM existentes. Não contém operação de submissão."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from app.backend.audit import atomic_json
from app.backend.storage import RunStore

DEFAULT = ROOT/'results/paired-aer-ibm-20261108'
CONFIRM = ROOT/'results/protocols/20261107T233046Z-6d048a1b4b85'
PILOT = ROOT/'results/campaigns/20261107-correlacoes-v3/hardware'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    """Contagens, QPY e calibração usados nos jobs, preservando sua identidade."""
    store=RunStore(ROOT/'results')
    primary=read(ROOT/'analysis/campaigns/20261108-resultados-ibm/analysis.json')['primary']
    reference={r['n']:r for r in primary}
    specs=[]
    for step in read(CONFIRM/'run.json')['steps']:
        if step['action']!='hardware':continue
        execution=read(ROOT/'results/executions'/step['execution_id']/'execution.json')
        original=read(ROOT/'results'/execution['result']['path'])['hardware_runs'][-1]
        manifest,summary,arrays=store.load(step['run_id'])
        hw=next(h for h in summary['hardware_runs'] if h['job_id']==original['job_id'])
        circuit=arrays[hw['circuit_artifact']['array_key']].tobytes()
        if hashlib.sha256(circuit).hexdigest()!=hw['circuit_sha256']:
            raise ValueError('Hash do QPY N4 não confere')
        specs.append({'n':4,'job_id':hw['job_id'],'config':manifest['config_input'],
            'trio':hw['indices'],'counts':arrays[hw['counts_key']].tolist(),'qpy_bytes':circuit,
            'calibration':hw['backend_properties'],'shots':hw['shots'],
            'qpy_sha256':hw['circuit_sha256'],'reference':reference[4]})
    plan=read(PILOT/'plan.json');collection=read(PILOT/'collection.json')
    if collection['plan_sha256']!=sha(PILOT/'plan.json'):
        raise ValueError('Plano da triagem alterado')
    for slot in collection['jobs']:
        candidate=next(c for c in plan['candidates'] if c['n']==slot['n'])
        counts_path=PILOT/(slot['slot']+'_counts.json');counts=read(counts_path)
        if sha(counts_path)!=slot['counts_sha256'] or counts['job_id']!=slot['job_id']:
            raise ValueError('Contagens da triagem alteradas')
        specs.append({'n':slot['n'],'job_id':slot['job_id'],'config':candidate['config'],
            'trio':candidate['trio'],'counts':counts['counts'],
            'qpy_bytes':(PILOT/candidate['qpy_path']).read_bytes(),
            'calibration':read(PILOT/'backend_properties.json'),'shots':4096,
            'qpy_sha256':candidate['qpy_sha256'],'reference':reference[slot['n']]})
    if len(specs)!=30 or len({s['job_id'] for s in specs})!=30:
        raise ValueError('Esperados os 30 jobs distintos já concluídos')
    return specs


def capture(output):
    from app.backend import ibm_runtime
    from qiskit_ibm_runtime.quantum_program.converters.converters_1_1 import quantum_program_to_1_1
    logging.getLogger('qiskit_ibm_runtime').setLevel(logging.ERROR)
    output.mkdir(parents=True,exist_ok=True)
    specs=sources();client=None;entries=[]
    for index,spec in enumerate(specs):
        folder=output/'inputs'/spec['job_id'];folder.mkdir(parents=True,exist_ok=True)
        marker=folder/'capture.json'
        if marker.exists():
            old=read(marker)
            if any(sha(folder/name)!=value for name,value in old['files_sha256'].items()):
                raise ValueError('Captura arquivada foi alterada')
            entries.append(old);continue
        if client is None:client=ibm_runtime._service()
        job=client.job(spec['job_id'])
        status=job.status()
        if str(getattr(status,'value',status)).upper()!='DONE':
            raise ValueError('Job ainda não concluído')
        raw=job.inputs;program=raw['quantum_program'];result=job.result()
        if len(program.items)!=1 or program.items[0].shape!=(32,):
            raise ValueError('Quantidade de randomizações inesperada')
        if program.shots*32!=spec['shots']:
            raise ValueError('Shots reais não correspondem ao registro')
        remote_counts=np.zeros(1<<spec['n'],dtype=np.int64)
        for bitstring,count in result[0].data.meas.get_counts().items():
            remote_counts[int(bitstring.replace(' ',''),2)]=count
        np.testing.assert_array_equal(remote_counts,spec['counts'])
        options=result.metadata['options']
        if not options['twirling']['enable_gates'] or options['twirling']['enable_measure']:
            raise ValueError('Política de twirling diferente da prevista')
        if options['dynamical_decoupling']['enable']:
            raise ValueError('Desacoplamento dinâmico inesperado')
        model=quantum_program_to_1_1(program,raw['options'])
        (folder/'program.json').write_text(model.model_dump_json())
        (folder/'base.qpy').write_bytes(spec['qpy_bytes'])
        if sha(folder/'base.qpy')!=spec['qpy_sha256']:
            raise ValueError('Circuito base alterado')
        atomic_json(folder/'calibration.json',spec['calibration'])
        atomic_json(folder/'case.json',{key:value for key,value in spec.items() if key not in ('qpy_bytes','calibration')})
        atomic_json(folder/'metadata.json',json.loads(json.dumps({'job_id':spec['job_id'],
            'options':options,'shots_per_randomization':program.shots,'num_randomizations':32,
            'pub_metadata':result[0].metadata,'metrics':job.metrics(),
            'samplex_inputs':list(program.items[0].samplex_arguments),
            'server_random_seed_available':False},default=str)))
        entry={'job_id':spec['job_id'],'n':spec['n'],'shots':spec['shots'],
            'num_randomizations':32,'shots_per_randomization':program.shots,
            'input_path':str(folder.relative_to(output)),
            'files_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}}
        atomic_json(marker,entry);entries.append(entry)
        print(f'Capturado {index+1}/30: N{spec["n"]} {spec["job_id"]}, 32 × {program.shots} shots',flush=True)
    atomic_json(output/'capture_manifest.json',{'status':'captured','read_only':True,
        'ibm_jobs_submitted':0,'source_script_sha256':sha(Path(__file__)),'jobs':entries})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT)
    capture(parser.parse_args().output.resolve())
