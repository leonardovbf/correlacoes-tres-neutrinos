#!/usr/bin/env python3
"""Bounded prospective IBM confirmation, with distinct calibration windows and resumable IDs."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
from qiskit import qpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'analysis')]
from app.backend import ibm_runtime
from app.backend.audit import atomic_json,safe_error
from run_correlation_noise import c3,marginal

SOURCE=ROOT/'results/feedback-revision-20261109'
DEFAULT=ROOT/'results/hardware-confirmation-20261110'
TAG='feedback-v4-confirmation-20261110'

def now():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):atomic_json(path,data)


def validate_plan(plan,source):
    policy=plan['policy']
    expected={'maximum_jobs':20,'pubs_per_job':2,'shots_per_pub':4096,'total_shots':163840,
        'independent_blocks':20,'calibration_windows':5,'blocks_per_window':4}
    if any(policy.get(k)!=v for k,v in expected.items()):raise ValueError('Budget or window policy differs from authorized plan')
    if len(plan['jobs'])!=20 or {c['n'] for c in plan['cases']}!={6,8}:raise ValueError('Unexpected job/case count')
    if policy['twirling']!={'enable_gates':True,'enable_measure':False,'num_randomizations':32,'shots_per_randomization':128}:
        raise ValueError('Unexpected twirling policy')
    circuits={}
    for case in plan['cases']:
        path=source/case['qpy']
        if sha(path)!=case['qpy_sha256']:raise ValueError('Archived QPY hash changed')
        with path.open('rb') as stream:circuit=qpy.load(stream)[0]
        if circuit.num_clbits!=case['n']:raise ValueError('Unexpected classical bits')
        if len([i for i in circuit.data if i.operation.name=='measure'])!=case['n']:raise ValueError('Unexpected measurement count')
        circuits[case['n']]=circuit
    for b,j in enumerate(plan['jobs']):
        if j['block']!=b or j['calibration_window']!=b//4 or j['total_shots']!=8192:
            raise ValueError('Job budget or calibration window changed')
        if j['pub_order']!=([6,8] if b%2==0 else [8,6]):raise ValueError('PUB ordering changed')
    return circuits


def validate_backend(backend,circuits):
    if backend.name!='ibm_kingston' or not backend.status().operational:raise ValueError('Authorized backend is not operational')
    if getattr(backend.configuration(),'simulator',False):raise ValueError('A physical backend is required')
    for circuit in circuits.values():
        for item in circuit.data:
            name=item.operation.name
            if name=='barrier':continue
            qubits=tuple(circuit.find_bit(q).index for q in item.qubits)
            if not backend.target.instruction_supported(operation_name=name,qargs=qubits):
                raise ValueError(f'Archived instruction unsupported: {name}{qubits}')


def fingerprint(properties,circuits):
    """Only the used physical qubits and native gate calibrations define a new window."""
    used=set();gates=set()
    for circuit in circuits.values():
        for item in circuit.data:
            if item.operation.name=='barrier':continue
            qubits=tuple(circuit.find_bit(q).index for q in item.qubits);used.update(qubits)
            gates.add((item.operation.name,qubits))
    names={'T1','T2','frequency','readout_error','prob_meas1_prep0','prob_meas0_prep1','init_error'}
    selected=[]
    for g in properties['gates']:
        if (g['gate'],tuple(g['qubits'])) not in gates:continue
        selected.append({'gate':g['gate'],'qubits':g['qubits'],
            'parameters':sorted([p for p in g['parameters'] if p['name'] in {'gate_error','gate_length'}],key=lambda p:p['name'])})
    relevant={'qubits':{str(q):sorted([p for p in properties['qubits'][q] if p['name'] in names],key=lambda p:p['name']) for q in sorted(used)},
        'gates':sorted(selected,key=lambda g:(g['gate'],tuple(g['qubits'])))}
    return hashlib.sha256(json.dumps(relevant,sort_keys=True,default=str).encode()).hexdigest()


def prepare_program(circuits,order,block,backend=None):
    from qiskit_ibm_runtime.executor_sampler.prepare import prepare
    from qiskit_ibm_runtime.options_models import SamplerOptions
    options=SamplerOptions()
    options.twirling.enable_gates=True;options.twirling.enable_measure=False
    options.twirling.num_randomizations=32;options.twirling.shots_per_randomization=128
    options.twirling.strategy='active-accum';options.dynamical_decoupling.enable=False
    options.twirling.group='pauli';options.max_execution_time=60
    options.environment.job_tags=[TAG,f'{TAG}-block-{block:02d}',f'{TAG}-window-{block//4}']
    program,executor_options=prepare([circuits[n] for n in order],options,shots=4096,backend=backend)
    # Exactly the same semantic role set by Sampler.run() in the pinned SDK.
    program._semantic_role='sampler_v2'
    if program.shots!=128 or len(program.items)!=2 or any(tuple(item.shape)!=(32,) for item in program.items):
        raise ValueError('SDK did not preserve two PUBs and 32x128 shots')
    if [item.circuit.num_clbits for item in program.items]!=order:raise ValueError('SDK changed PUB ordering')
    return program,executor_options


def initialize(output,source=SOURCE):
    plan_path=source/'hardware_confirmation_plan.json';plan=read(plan_path);circuits=validate_plan(plan,source)
    output.mkdir(parents=True,exist_ok=True)
    identity={'source_plan_sha256':sha(plan_path),'runner_sha256':sha(Path(__file__)),
        'backend':'ibm_kingston','campaign_tag':TAG,'maximum_jobs':20,'shots_per_job':8192,'total_shots_cap':163840,
        'window_policy':'4 jobs per window; next window only after all prior jobs DONE and used-qubit/gate calibration fingerprint changes; never silently collapse to one calibration',
        'submission_policy':'save submitting before POST, save ID immediately; uncertain POST stops automatic submission; no failed-job replacement',
        'cases':[{k:c[k] for k in ['n','config','trio','exact','psa_full_support','qpy','qpy_sha256']} for c in plan['cases']],
        'source_root':str(source.relative_to(ROOT))}
    path=output/'execution_plan.json'
    if path.exists() and read(path)!=identity:raise ValueError('Execution inputs changed; preserve the current campaign')
    save(path,identity)
    state_path=output/'state.json'
    if not state_path.exists():
        save(state_path,{'status':'prepared','created_utc':now(),'execution_plan_sha256':sha(path),'windows':[],
            'jobs':[{**j,'slot':f'{TAG}-block-{j["block"]:02d}','job_id':None,'status':'planned'} for j in plan['jobs']],
            'submitted_jobs':0,'reserved_shots':0,'stop_requested':False})
    state=read(state_path)
    if state['execution_plan_sha256']!=sha(path):raise ValueError('Execution plan hash changed')
    return plan,circuits,state


def collect(output,client,state):
    for slot in state['jobs']:
        if not slot['job_id'] or slot['status']=='DONE':continue
        job=client.job(slot['job_id']);status=job.status();slot['status']=str(getattr(status,'value',status)).upper()
        if slot['status']!='DONE':continue
        result=job.result()
        if len(result)!=2:raise ValueError('IBM returned an unexpected PUB count')
        counts={}
        for pub,n in zip(result,slot['pub_order']):
            vector=np.zeros(1<<n,dtype=np.int64)
            for bitstring,value in pub.data.meas.get_counts().items():vector[int(bitstring.replace(' ',''),2)]=value
            if vector.sum()!=4096:raise ValueError('IBM returned unexpected shot count')
            counts[str(n)]=vector.tolist()
        path=output/'jobs'/slot['slot'];path.mkdir(parents=True,exist_ok=True)
        payload={'job_id':slot['job_id'],'block':slot['block'],'pub_order':slot['pub_order'],'counts':counts,'collected_utc':now()}
        save(path/'counts.json',payload);slot['counts_path']=str((path/'counts.json').relative_to(output));slot['counts_sha256']=sha(path/'counts.json')
        save(path/'runtime_metadata.json',json.loads(json.dumps({'metrics':job.metrics(),'metadata':result.metadata,'pub_metadata':[pub.metadata for pub in result]},default=str)))
        from qiskit_ibm_runtime.quantum_program.converters.converters_1_1 import quantum_program_to_1_1
        inputs=job.inputs;remote=quantum_program_to_1_1(inputs['quantum_program'],inputs['options'])
        (path/'actual_program.json').write_text(remote.model_dump_json())
        slot['collected_utc']=now();print('Collected',slot['slot'],slot['job_id'],flush=True)
        save(output/'state.json',state)


def eligible_window(state,current_fingerprint):
    """All 20 jobs remain in one immutable budget; never advance on result significance."""
    if any(j['status'] in ['submitting','submission_uncertain'] for j in state['jobs']):return None,'submission_uncertain'
    if any(j['status'] in ['ERROR','CANCELLED','FAILED'] for j in state['jobs']):return None,'hardware_job_failed_no_auto_replacement'
    for window in range(5):
        jobs=[j for j in state['jobs'] if j['calibration_window']==window]
        if all(j['status']=='DONE' for j in jobs):continue
        if any(j['job_id'] for j in jobs):
            if any(not j['job_id'] for j in jobs):return window,'resume_same_window'
            return None,'awaiting_current_window_results'
        fingerprints={w['fingerprint'] for w in state['windows']}
        if current_fingerprint in fingerprints:return None,'awaiting_new_calibration'
        return window,'new_calibration_window'
    return None,'all_jobs_done'


def submit_one(output,backend,circuits,state,slot):
    from qiskit_ibm_runtime.executor import Executor
    from qiskit_ibm_runtime.quantum_program.converters.converters_1_1 import quantum_program_to_1_1
    if (output/'STOP').exists():raise ValueError('Future submissions stopped by user')
    if slot['job_id'] or slot['status'] not in ['planned']:raise ValueError('Not a fresh planned slot')
    ids=[s['job_id'] for s in state['jobs'] if s['job_id']]
    if len(ids)>=20 or len(set(ids))!=len(ids) or (len(ids)+1)*8192>163840:raise ValueError('Budget or unique-ID cap violated')
    program,options=prepare_program(circuits,slot['pub_order'],slot['block'],backend)
    folder=output/'jobs'/slot['slot'];folder.mkdir(parents=True,exist_ok=True)
    (folder/'submitted_program.json').write_text(quantum_program_to_1_1(program,options).model_dump_json())
    slot.update(status='submitting',started_utc=now());save(output/'state.json',state)
    try:
        job=Executor(mode=backend,options=options).run(program)
        identifier=job.job_id()
        if not identifier or identifier in ids:raise ValueError('Missing or duplicate IBM job ID')
        slot.update(job_id=identifier,status='submitted',submitted_utc=now())
        state['submitted_jobs']=sum(bool(s['job_id']) for s in state['jobs']);state['reserved_shots']=state['submitted_jobs']*8192
        save(output/'state.json',state)
        print('Submitted',slot['slot'],identifier,'PUBs',slot['pub_order'],'shots 8192',flush=True)
    except Exception as exc:
        slot.update(status='submission_uncertain',error=safe_error(exc));save(output/'state.json',state);raise


def analyze(output,state,plan):
    if not all(j['status']=='DONE' for j in state['jobs']):return
    save(output/'analysis.json',compute_analysis(output,state,plan))


def compute_analysis(output,state,plan):
    rng=np.random.default_rng(950000);weights=rng.multinomial(20,np.ones(20)/20,size=10000);rows=[]
    for case in plan['cases']:
        n=case['n'];blocks=[]
        for job in state['jobs']:
            if sha(output/job['counts_path'])!=job['counts_sha256']:raise ValueError('Hardware counts changed')
            counts=np.asarray(read(output/job['counts_path'])['counts'][str(n)]);blocks.append(marginal(counts,case['trio']))
        blocks=np.array(blocks);total=blocks.sum(axis=0);estimate=float(c3(total/total.sum()))
        samples=weights@blocks;values=c3(samples/samples.sum(axis=1,keepdims=True));comparisons={}
        for name,baseline in [('PSA',case['psa_full_support']),('zero',0.)]:
            delta=np.abs(values-case['exact'])-abs(baseline-case['exact']);ci=np.quantile(delta,[.00625,.99375])+[-1e-5,1e-5]
            comparisons[name]={'difference':abs(estimate-case['exact'])-abs(baseline-case['exact']),'simultaneous_CI':ci.tolist(),'passes':bool(ci[1]<0)}
        rows.append({'n':n,'shots':int(total.sum()),'estimate':estimate,'exact':case['exact'],'psa':case['psa_full_support'],
            'comparisons':comparisons,'estimate_CI98_75':np.quantile(values,[.00625,.99375]).tolist(),
            'calibration_windows':5,'scope':'two fixed points, independent confirmation data only; not computational quantum advantage'})
    return {'status':'complete','cases':rows,'all_four_comparisons_pass':all(v['passes'] for r in rows for v in r['comparisons'].values()),
        'multiplicity':'four two-sided 98.75% intervals; familywise Bonferroni alpha .05','bootstrap':'joint resampling of the 20 two-PUB jobs; no within-job multinomial resampling',
        'confirmation_jobs':20,'new_shots':163840}


def close(a,b):
    if isinstance(a,dict):return a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,float) or isinstance(b,float):return abs(a-b)<=1e-12
    return a==b


def verify(output):
    """Offline audit of a finished campaign: budget, IDs, hashes, calibration windows and the published analysis."""
    state=read(output/'state.json');plan=read(output/'execution_plan.json');jobs=state['jobs']
    if state['execution_plan_sha256']!=sha(output/'execution_plan.json'):raise ValueError('Execution plan hash changed')
    ids=[j['job_id'] for j in jobs]
    if len(jobs)!=20 or not all(ids) or len(set(ids))!=20:raise ValueError('Expected 20 distinct IBM job IDs')
    if state['submitted_jobs']!=20 or state['reserved_shots']!=163840:raise ValueError('Budget differs from authorized plan')
    if any(j['status']!='DONE' for j in jobs):raise ValueError('Campaign has unfinished jobs')
    total=0
    for j in jobs:
        if j['pub_order']!=([6,8] if j['block']%2==0 else [8,6]):raise ValueError('PUB ordering changed')
        if sha(output/j['counts_path'])!=j['counts_sha256']:raise ValueError('Hardware counts changed')
        counts=read(output/j['counts_path'])['counts']
        if sorted(counts)!=['6','8'] or any(sum(v)!=4096 for v in counts.values()):raise ValueError('Unexpected PUB shots')
        total+=sum(sum(v) for v in counts.values())
    if total!=163840:raise ValueError('Total shots differ from budget')
    windows=state['windows']
    if len(windows)!=5 or len({w['fingerprint'] for w in windows})!=5:raise ValueError('Expected five distinct calibration windows')
    for w in windows:
        if sha(output/w['path'])!=w['sha256']:raise ValueError('Calibration archive changed')
    if not close(compute_analysis(output,state,plan),read(output/'analysis.json')):raise ValueError('Published analysis does not follow from archived counts')
    print('Hardware confirmation verified: 20 jobs, 163840 shots, 5 calibration windows, analysis recomputed',flush=True)


def export(output,destination):
    """Single immutable ZIP of the campaign folder plus a per-file SHA-256 manifest."""
    import shutil,zipfile
    verify(output)
    if destination.exists():raise ValueError('Preserve previous export; use a new destination')
    destination.mkdir(parents=True)
    files=sorted(p for p in output.rglob('*') if p.is_file() and p.name!='.runner.lock')
    path=destination/'data.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in files:archive.write(p,str(p.relative_to(output)))
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:raise ValueError('Archive corrupt')
    shutil.copy2(output/'analysis.json',destination/'analysis.json')
    save(destination/'archives.json',{'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'data_root':str(output.relative_to(ROOT)),
        'files_sha256':{str(p.relative_to(output)):sha(p) for p in files},'runner_sha256':sha(Path(__file__))})
    print('Exported',len(files),'files:',destination,flush=True)


def tick(output,client,source=SOURCE,allow_hardware=False):
    if not allow_hardware:raise ValueError('Explicit --allow-hardware required for this bounded execution')
    plan,circuits,state=initialize(output,source)
    if state.get('stop_requested') or (output/'STOP').exists():return 'stopped_by_user'
    collect(output,client,state)
    if all(j['status']=='DONE' for j in state['jobs']):
        analyze(output,state,plan);state['status']='complete';save(output/'state.json',state);return 'complete'
    backend=client.backend('ibm_kingston');validate_backend(backend,circuits)
    properties=backend.properties(refresh=True);payload=json.loads(json.dumps(properties.to_dict(),default=str))
    used={c.find_bit(q).index for c in circuits.values() for item in c.data if item.operation.name!='barrier' for q in item.qubits}
    if used.intersection(properties.faulty_qubits()):raise ValueError('An archived physical qubit is currently faulty')
    for c in circuits.values():
        for item in c.data:
            if item.operation.name not in {'cz','sx','x'}:continue
            qs=tuple(c.find_bit(q).index for q in item.qubits)
            if not properties.is_gate_operational(item.operation.name,qs):raise ValueError('An archived native gate is currently faulty')
    current=fingerprint(payload,circuits);window,reason=eligible_window(state,current)
    if window is not None:
        entry=next((w for w in state['windows'] if w['window']==window),None)
        if entry is None:
            entry={'window':window,'fingerprint':current,'captured_utc':now(),'last_update':str(properties.last_update_date)}
            path=output/'calibrations'/f'window_{window}.json';save(path,payload)
            entry.update(path=str(path.relative_to(output)),sha256=sha(path));state['windows'].append(entry)
        elif entry['fingerprint']!=current:
            raise ValueError('Calibration changed during partial window; preserve state and review before remaining submissions')
        save(output/'state.json',state)
        for slot in state['jobs']:
            if (output/'STOP').exists():
                state['stop_requested']=True;state['status']='stopped_by_user';save(output/'state.json',state);return 'stopped_by_user'
            if slot['calibration_window']==window and not slot['job_id']:submit_one(output,backend,circuits,state,slot)
        reason='awaiting_current_window_results'
    state['status']=reason;state['last_poll_utc']=now();state['latest_calibration_fingerprint']=current
    state['submitted_jobs']=sum(bool(j['job_id']) for j in state['jobs']);state['reserved_shots']=state['submitted_jobs']*8192
    save(output/'state.json',state);print('Status:',reason,'submitted',state['submitted_jobs'],'/20',flush=True)
    return reason


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['check','tick','watch','status','stop','verify','export'])
    parser.add_argument('--output',type=Path,default=DEFAULT);parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--release',type=Path,default=ROOT/'analysis/campaigns/20261110-hardware-confirmation')
    parser.add_argument('--allow-hardware',action='store_true');parser.add_argument('--poll-seconds',type=int,default=300)
    args=parser.parse_args();output=args.output.resolve();source=args.source.resolve()
    logging.getLogger('qiskit_ibm_runtime').setLevel(logging.ERROR)
    if args.command=='status':
        s=read(output/'state.json');print(json.dumps({k:v for k,v in s.items() if k!='jobs'},indent=2));return
    if args.command=='stop':
        (output/'STOP').write_text(now());s=read(output/'state.json');s['stop_requested']=True;save(output/'state.json',s);print('Future submissions disabled; submitted jobs are preserved.');return
    if args.command=='verify':verify(output);return
    if args.command=='export':export(output,args.release.resolve());return
    plan,circuits,state=initialize(output,source)
    if args.command=='check':
        for order in [[6,8],[8,6]]:prepare_program(circuits,order,0)
        print('Offline SDK: two PUBs, 32x128, 8192 shots/job, 20-job cap verified');return
    if not args.allow_hardware:raise ValueError('Missing --allow-hardware')
    if args.poll_seconds<60:raise ValueError('Minimum polling interval is 60 seconds')
    with (output/'.runner.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('An executor already owns this campaign')
        save(output/'runner.json',{'pid':os.getpid(),'started_utc':now(),'poll_seconds':args.poll_seconds,
            'maximum_days':14,'maximum_jobs':20,'total_shots_cap':163840,'window_policy':'wait for distinct used-qubit calibrations'})
        client=None;started=time.monotonic()
        while True:
            try:
                if client is None:client=ibm_runtime._service()
                status=tick(output,client,source,allow_hardware=True)
            except Exception as exc:
                save(output/'last_error.json',{'utc':now(),'error':safe_error(exc)})
                if any(j['status'] in ['submission_uncertain','submitting'] for j in read(output/'state.json')['jobs']):raise
                if args.command=='tick':raise
                print('Read/preflight error; no automatic replacement:',safe_error(exc)['message'],flush=True);client=None;status='read_error'
            if args.command=='tick' or status in ['complete','stopped_by_user','submission_uncertain','hardware_job_failed_no_auto_replacement']:break
            if time.monotonic()-started>14*86400:
                s=read(output/'state.json');s['status']='watch_deadline_reached';save(output/'state.json',s);break
            time.sleep(args.poll_seconds)

if __name__=='__main__':main()
