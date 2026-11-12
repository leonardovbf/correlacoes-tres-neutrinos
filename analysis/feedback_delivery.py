#!/usr/bin/env python3
"""Metadata, bounded prospective hardware design and portable scientific export."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
from qiskit import qpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'analysis'),str(ROOT/'scripts')]
from run_feedback_revision import initialize,read,save,sha,DEFAULT,DESIGN
from app.backend.storage import RunStore
from neutrinos.study_analysis import independent_exact_check,connected,metrics
from feedback_statistics import slope,wilson,intervals
from run_correlation_noise import c3,marginal


def csv_file(path,rows):
    with path.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def hardware_archive(output):
    folder=output/'ibm_archive';folder.mkdir(exist_ok=True);store=RunStore(ROOT/'results')
    runs={}
    for path in (ROOT/'results/protocols').glob('*/run.json'):
        for step in read(path).get('steps',[]):
            if step['action']=='hardware' and step.get('run_id'):runs[step['run_id']]=True
    jobs={};resources=[]
    for run in sorted(runs):
        manifest,summary=store.load_metadata(run)
        version=(ROOT/'results'/run/'current').read_text().strip();source=ROOT/'results'/run/'versions'/version/'moments.npz'
        with np.load(source,allow_pickle=False) as arrays:
            for hw in summary.get('hardware_runs',[]):
                if hw['job_id'] in jobs:continue
                if hw.get('status')!='DONE':continue
                counts=arrays[hw['counts_key']].copy()
                if counts.sum()!=hw['shots']:raise ValueError('Archived hardware count budget mismatch')
                entry={k:v for k,v in hw.items() if k!='backend_properties'}
                entry.update(config=manifest['config_input'],counts=counts.tolist(),source_run_id=run,source_version=version)
                if hw.get('backend_properties'):
                    blob=json.dumps(hw['backend_properties'],sort_keys=True,separators=(',',':')).encode()
                    digest=hashlib.sha256(blob).hexdigest();path=folder/'calibrations'/(digest+'.json');path.parent.mkdir(exist_ok=True)
                    if not path.exists():path.write_bytes(blob)
                    entry['calibration_file']=str(path.relative_to(output));entry['calibration_sha256']=digest
                if hw.get('circuit_artifact'):
                    blob=arrays[hw['circuit_artifact']['array_key']].tobytes();digest=hashlib.sha256(blob).hexdigest()
                    if digest!=hw['circuit_sha256']:raise ValueError('Archived QPY changed')
                    path=folder/'circuits'/(digest+'.qpy');path.parent.mkdir(exist_ok=True)
                    if not path.exists():path.write_bytes(blob)
                    entry['circuit_file']=str(path.relative_to(output))
                jobs[hw['job_id']]=entry
    # The N6/N8 pilot used the direct runner, outside RunStore.
    capture=ROOT/'results/paired-aer-ibm-20261108'
    for e in read(capture/'capture_manifest.json')['jobs']:
        if e['job_id'] in jobs:continue
        root=capture/e['input_path'];case=read(root/'case.json')
        with (root/'base.qpy').open('rb') as stream:circuit=qpy.load(stream)[0]
        path=folder/'circuits'/(sha(root/'base.qpy')+'.qpy');path.parent.mkdir(exist_ok=True)
        if not path.exists():shutil.copy2(root/'base.qpy',path)
        entry={'job_id':e['job_id'],'backend':'ibm_kingston','status':'DONE','config':case['config'],
            'counts':case['counts'],'shots':case['shots'],'steps':2,'interval_index':1,'tau':case['reference']['tau'],
            'role':'exploratory_pilot','indices':case['trio'],'two_qubit_gates':int(circuit.count_ops().get('cz',0)),
            'transpiled_depth':circuit.depth(),'circuit_sha256':sha(root/'base.qpy'),'circuit_file':str(path.relative_to(output)),
            'transpilation':{'physical_qubits':circuit.layout.final_index_layout()},
            'runtime_options':read(root/'metadata.json')['options']}
        blob=json.dumps(read(root/'calibration.json'),sort_keys=True,separators=(',',':')).encode()
        digest=hashlib.sha256(blob).hexdigest();calibration=folder/'calibrations'/(digest+'.json');calibration.parent.mkdir(exist_ok=True)
        if not calibration.exists():calibration.write_bytes(blob)
        entry.update(calibration_file=str(calibration.relative_to(output)),calibration_sha256=digest)
        jobs[e['job_id']]=entry
    for job in jobs.values():
        cfg=job['config'];steps=job['steps'];interval=job['interval_index'];runtime=job.get('runtime_options',{})
        calibration=bool(job.get('calibration_reference',False))
        resources.append({'job_id':job['job_id'],'n':cfg['n'],'mu':cfg['mu'],'evolution_tau':0. if calibration else job['tau'],
            'parent_experiment_tau':job['tau'],'calibration_reference':calibration,
            'role':job.get('role'),'shots':job['shots'],'steps_per_interval':0 if calibration else steps,'interval_index':0 if calibration else interval,
            'total_trotter_steps':0 if calibration else steps*interval,'native_depth':job['transpiled_depth'],
            'two_qubit_gates':job['two_qubit_gates'],'logical_to_physical':json.dumps(job.get('transpilation',{}).get('physical_qubits')),
            'runtime_options':json.dumps(runtime,sort_keys=True),'qpy_sha256':job.get('circuit_sha256')})
    if len(jobs)!=130:raise ValueError(f'Expected 120 stored historical jobs + 10 pilot jobs; found {len(jobs)}')
    save(output/'existing_ibm_jobs.json',{'status':'all_local_completed_hardware_archived','jobs':list(jobs.values()),
        'job_count':len(jobs),'new_submissions':0,'meaning':'120 historical RunStore jobs plus 10 direct pilot jobs; the latest 30 are a subset, not additional jobs.'})
    csv_file(output/'hardware_parameters.csv',resources)


def controls(output):
    reports=read(output/'original_controls.json');by_name={Path(r['source']).stem:r for r in reports};rows=[]
    def add(label,report,predicate,limit):
        values=[c for c in by_name[report]['checks'] if predicate(c)]
        if not values:raise ValueError('Missing numerical control: '+label)
        largest=max(values,key=lambda c:c['value'])
        rows.append({'control':label,'observed':largest['value'],'limit':limit,'passed':largest['value']<=limit,
            'source':by_name[report]['source'],'source_sha256':by_name[report]['source_sha256'],'largest_case':largest['name']})
    add('Published reproduction exact','T00-reproducao-publicada',lambda c:'Figura 2(c): exact' in c['name'],.02)
    add('Published reproduction PSA','T00-reproducao-publicada',lambda c:'Figura 2(c): psa' in c['name'],.06)
    check=independent_exact_check()
    rows.append({'control':'Independent dense-vs-sparse exact state','observed':check['state_max_abs'],'limit':1e-10,'passed':check['state_max_abs']<=1e-10,
        'source':'src/neutrinos/study_analysis.py:independent_exact_check','source_sha256':sha(ROOT/'src/neutrinos/study_analysis.py'),'largest_case':'N4 independent construction'})
    add('Qiskit vs emulator','T04-qiskit',lambda c:c['name'].startswith('qiskit_') and '_tau' in c['name'],1e-10)
    add('RK4 refinement Pe','T02-integracao',lambda c:c['name'].endswith(('psa pe','mean pe')),1e-6)
    add('RK4 refinement cumulants','T02-integracao',lambda c:c['name'].endswith(('psa c2','psa c3','mean c2','mean c3')),1e-5)
    add('PSA supplementary seed standard error','T02-amostragem-suplementar',lambda c:'erro padrão PSA' in c['name'],.01)
    add('Trotter ideal C3 on original verification grid','T04-trotter',lambda c:c['name'].endswith('_t16'),.001)
    csv_file(output/'table4_controls.csv',rows);save(output/'table4_controls.json',rows)
    from app.backend.trotter_recovery import document
    changes=document()['changes'];save(output/'original_discretization_changes.json',changes)
    h1=[]
    for c in read(output/'original_h1.json')['cases']:
        requests=c['sources'];substeps=sorted({r['request']['substeps'] for r in requests});trajectories=sorted({r['request']['trajectories'] for r in requests})
        h1.append({'id':c['id'],'n':c['n'],'mu':c['mu'],'end':c['config']['t_max'],'points':c['config']['points'],
            'blocks':len(requests),'RK4_substeps':json.dumps(substeps),'trajectories_per_block':json.dumps(trajectories),
            'initial_flavors':json.dumps(c['config']['flavors']),'omega':json.dumps(c['config'].get('omega_values')),
            'geometry':'uniform','source_arrays':c['arrays'],'source_sha256':c['arrays_sha256']})
    csv_file(output/'classical_parameters.csv',h1)


def hardware_plan(output):
    if (output/'hardware_confirmation_plan.json').exists():return
    design=read(DESIGN)['hardware'];capture=ROOT/'results/paired-aer-ibm-20261108';manifest=read(capture/'capture_manifest.json')
    cases=[];folder=output/'confirmation_inputs';folder.mkdir(exist_ok=True)
    for n in [6,8]:
        entries=[e for e in manifest['jobs'] if e['n']==n];example=capture/entries[0]['input_path'];case=read(example/'case.json')
        counts=np.array([read(capture/e['input_path']/'case.json')['counts'] for e in entries])
        path=folder/f'n{n}.qpy';shutil.copy2(example/'base.qpy',path)
        cases.append({'n':n,'config':case['config'],'trio':case['trio'],'exact':case['reference']['exact'],
            'psa_full_support':case['reference']['psa_full_support'],'pilot_job_ids':[e['job_id'] for e in entries],
            'qpy':str(path.relative_to(output)),'qpy_sha256':sha(path),'pilot_counts':counts.tolist()})
    power=[];rng=np.random.default_rng(940000)
    for model in ['stationary_pooled_with_probability_uncertainty','empirical_job_heterogeneity_sensitivity']:
        success=[]
        for campaign in range(500):
            all_pass=True
            for c in cases:
                observed=np.array([marginal(np.asarray(row),c['trio']) for row in c['pilot_counts']])
                if model.startswith('stationary'):
                    p=rng.dirichlet(observed.sum(axis=0)+.5);future=rng.multinomial(4096,p,size=20)
                else:
                    p=observed/observed.sum(axis=1,keepdims=True);selected=p[rng.integers(0,len(p),size=20)]
                    future=rng.multinomial(4096,selected,size=20)
                weights=rng.multinomial(20,np.ones(20)/20,size=2000);draws=c3((weights@future)/81920)
                for reference in [c['psa_full_support'],0.]:
                    delta=np.abs(draws-c['exact'])-abs(reference-c['exact'])
                    if np.quantile(delta,.99375)+1e-5>=0:all_pass=False
            success.append(all_pass)
        k=sum(success);power.append({'model':model,'simulated_successes':k,'scenarios':500,'fraction':k/500,'MC_ci95':wilson(k,500),
            'scope':'prospective planning conditional on five pilot jobs per N; not guaranteed power or measured future calibration drift'})
    plan={'status':'prepared_not_submitted','policy':design,'design_sha256':sha(DESIGN),
        'cases':cases,'planning_sensitivity':power,
        'jobs':[{'block':b,'calibration_window':b//4,'pub_order':[6,8] if b%2==0 else [8,6],
            'shots_per_pub':4096,'total_shots':8192} for b in range(20)],
        'pre_execution_checks':['QPY hashes and logical measurements unchanged','target has all archived physical qubits and native instructions',
            'fresh calibration captured before each window','SDK accepts exactly two PUBs in one job with 4096 shots each',
            'maximum 20 jobs and 163840 signal shots; no automatic budget extension','replay Aer from same submitted program and current calibration',
            'no selection or stopping early according to observed significance'],
        'new_ibm_jobs_submitted':0}
    save(output/'hardware_confirmation_plan.json',plan)


def summarize(output):
    audit=read(output/'h1_audit.json');coverage=read(output/'coverage.json');h1=read(output/'h1_controlled.json');h2=read(output/'h2.json')
    controls(output);hardware_archive(output);hardware_plan(output)
    csv_file(output/'h1_audit_summary.csv',[{'n':r['n'],'mu':r['mu'],'D':r['central_D_R3_R2'][0],
        'original_outside_interval':r['original_outside_own_interval'],'bootstrap_bias_D':r['bootstrap_mean_bias_D'],
        **{m+'_ci95':json.dumps(r['intervals']['D'][m]) for m in ['percentile','basic','BCa']}} for r in audit['cases']])
    csv_file(output/'h1_controlled_summary.csv',[{'n':r['n'],'mu':r['mu'],'Pe_rmse':r['metrics']['pe']['rmse'],
        'C2_rmse':r['metrics']['c2']['rmse'],'C3_rmse':r['metrics']['c3']['rmse'],'R2':r['metrics']['c2']['normalized_rmse'],
        'R3':r['metrics']['c3']['normalized_rmse'],'D':r['D'],'PSA_beats_C3_zero':r['psa_beats_zero']} for r in h1['cases']])
    csv_file(output/'h2_summary.csv',[{'family':r['family'],'level':r['level'],'p1':r['p1'],'p2':r['p2'],'readout':r['readout'],
        **{m+'_expected':r['expected_c3'][m] for m in ['raw','mitigated']},
        **{m+'_estimate':r['observed'][m]['estimate'] for m in ['raw','mitigated']},
        **{m+'_equivalent':r['observed'][m]['primary_equivalent'] for m in ['raw','mitigated']},
        **{m+'_decision_probability':r['decision_probability'][m]['probability'] for m in ['raw','mitigated']}} for r in h2['rows']])
    save(output/'summary.json',{'status':'local_feedback_experiments_complete','original_H1_cells':len(audit['cases']),
        'bootstrap_anomalies_reproduced':audit['original_anomalies'],'coverage_campaigns':400,'controlled_H1_cells':len(h1['cases']),
        'h2_conditions':len(h2['rows']),'h2_finite_shot_campaigns':len(h2['rows'])*100,
        'historical_IBM_jobs_preserved':read(output/'existing_ibm_jobs.json')['job_count'],
        'new_IBM_jobs':0,'confirmation':'prepared with explicit caps; not submitted',
        'statistical_scope':'Weak-signal percentile/basic/BCa intervals under-cover in N4 validation; do not make global H1 claims from original 14/15 or 10/10 counts. Deterministic controlled grid supports only its stated regimes.'})


def verify(output):
    """Portable reanalysis from archived moments, counts and bootstrap draws; no original RunStore."""
    checked=0
    for c in read(output/'original_h1.json')['cases']:
        if sha(output/c['arrays'])!=c['arrays_sha256']:raise ValueError('Original block capture hash changed')
        report=read(output/'h1_audit'/f'{c["id"]}.json')
        with np.load(output/c['arrays']) as a:
            pair,triple=connected(*(a[k].mean(axis=0) for k in ['m1','m2','m3']),c['n'])
            r2=metrics(a['reference_c2'],pair)['normalized_rmse'];r3=metrics(a['reference_c3'],triple)['normalized_rmse']
        np.testing.assert_allclose([r3-r2,r3,r2],report['central_D_R3_R2'],atol=1e-12,rtol=0)
        with np.load(output/report['arrays']) as a:
            ci=intervals(a['central'][0],a['draws'][:,0],a['jackknife'][:,0])
            for method in ['percentile','basic','BCa']:np.testing.assert_allclose(ci[method],report['intervals']['D'][method],atol=1e-12)
        checked+=1
    # Reconstruct every original N4/mu=.1 block from its raw sampled labels,
    # independently of the already aggregated moments used above.
    case=next(c for c in read(output/'original_h1.json')['cases'] if c['n']==4 and c['mu']==.1)
    from run_correlation_search import initial_support
    from neutrinos.sim import ExperimentConfig,_evolve_spins
    cfg=ExperimentConfig.from_dict(case['config']);substeps=case['sources'][0]['request']['substeps']
    z=_evolve_spins(cfg,initial_support(cfg,0,256),substeps)[...,2]
    with np.load(output/case['arrays']) as a:
        weights=np.array([np.bincount(row,minlength=256) for row in a['raw_initial_labels']])/4096
        features=[z,np.prod(z[:,:,cfg.pair_index],axis=-1),np.prod(z[:,:,cfg.trio_index],axis=-1)]
        for k,feature in zip(['m1','m2','m3'],features):
            regenerated=(weights@feature.transpose(1,0,2).reshape(256,-1)).reshape(20,201,-1)
            np.testing.assert_allclose(regenerated,a[k],atol=2e-13,rtol=0)
    for row in read(output/'h2.json')['rows']:
        if sha(output/row['arrays'])!=row['arrays_sha256']:raise ValueError('H2 counts hash changed')
        from feedback_noise import trio,analyze_counts
        with np.load(output/row['arrays']) as a:
            counts={k:a[k] for k in ['raw','signal','zero','one']}
            expected,_,_=analyze_counts(counts,read(output/'h2.json')['context']['case']['reference']['exact'],
                read(output/'h2.json')['context']['case']['reference']['psa_full_support'],row['seed']+1)
        for method in ['raw','mitigated']:
            np.testing.assert_allclose(expected[method]['estimate'],row['observed'][method]['estimate'],atol=1e-13)
            np.testing.assert_allclose(expected[method]['difference_exact_ci95'],row['observed'][method]['difference_exact_ci95'],atol=1e-13)
        checked+=1
    for row in read(output/'h1_controlled.json')['cases']:
        with np.load(output/row['arrays']) as a:
            exact2,exact3=connected(*(a['exact_'+k] for k in ['m1','m2','m3']),row['n'])
            psa2,psa3=connected(*(a['psa_'+k] for k in ['m1','m2','m3']),row['n'])
            for key,ref,value in [('c2',exact2,psa2),('c3',exact3,psa3)]:
                np.testing.assert_allclose(metrics(ref,value)['normalized_rmse'],row['metrics'][key]['normalized_rmse'],atol=1e-12)
        checked+=1
    for job in read(output/'existing_ibm_jobs.json')['jobs']:
        if sum(job['counts'])!=job['shots']:raise ValueError('Hardware budget changed')
        if sha(output/job['circuit_file'])!=job['circuit_sha256']:raise ValueError('Hardware QPY hash changed')
        if sha(output/job['calibration_file'])!=job['calibration_sha256']:raise ValueError('Hardware calibration hash changed')
        checked+=1
    print('Portable reanalysis verified:',checked,'cases/jobs',flush=True)
    return checked


def export(output,destination):
    if destination.exists():raise ValueError('Preserve previous export; use a new --release')
    required=['summary.json','h1_audit.json','coverage.json','h1_controlled.json','h2.json','hardware_confirmation_plan.json','existing_ibm_jobs.json']
    for file in required:
        if not (output/file).exists():raise ValueError('Incomplete revision: '+file)
    destination.mkdir(parents=True)
    # Keep every part below 45 MiB; files are not lossy rounded or dropped.
    files=sorted(p for p in output.rglob('*') if p.is_file());groups=[];current=[];size=0
    for p in files:
        length=p.stat().st_size
        if current and size+length>45*1024**2:groups.append(current);current=[];size=0
        current.append(p);size+=length
    if current:groups.append(current)
    parts=[]
    for index,group in enumerate(groups):
        path=destination/f'data-part-{index+1:02d}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for p in group:archive.write(p,str(p.relative_to(output)))
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:raise ValueError('Archive corrupt')
        parts.append({'file':path.name,'sha256':sha(path),'files':len(group),'bytes':path.stat().st_size})
    for name in ['summary.json','hardware_confirmation_plan.json','h1_audit_summary.csv','h1_controlled_summary.csv','h2_summary.csv','table4_controls.csv','hardware_parameters.csv','classical_parameters.csv']:
        shutil.copy2(output/name,destination/name)
    source=[ROOT/'analysis/run_feedback_revision.py',ROOT/'analysis/feedback_statistics.py',ROOT/'analysis/feedback_noise.py',Path(__file__),DESIGN,ROOT/'tests/test_feedback_revision.py',ROOT/'requirements-research.lock']
    for path in source:
        target=destination/'sources'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    save(destination/'archives.json',{'parts':parts,'files_sha256':{str(p.relative_to(output)):sha(p) for p in files},'data_root':'results/feedback-revision-20261109',
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in source},'all_original_data_preserved':True})
    print('Exported',len(files),'files in',len(parts),'ZIP parts:',destination,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['summarize','verify','export'])
    parser.add_argument('--output',type=Path,default=DEFAULT)
    parser.add_argument('--release',type=Path,default=ROOT/'analysis/campaigns/20261109-feedback-v4')
    args=parser.parse_args();out=args.output.resolve()
    if args.stage=='summarize':summarize(out)
    elif args.stage=='verify':verify(out)
    else:export(out,args.release.resolve())
