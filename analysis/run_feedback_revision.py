#!/usr/bin/env python3
"""Local, resumable experiments addressing the Entrega 2 feedback; no IBM submission."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'analysis')]
from app.backend.audit import atomic_json
from neutrinos.sim import ExperimentConfig, _evolve_spins, _from_trajectories, classical_exact
from neutrinos.study_analysis import metrics
from feedback_statistics import (statistics,bootstrap_statistics,intervals,weighted_statistics,wilson,slope,first_loss)
from run_correlation_search import complete_psa,initial_support,config as search_config

DESIGN=ROOT/'configs/protocols/revisao_feedback_v4/design.json'
DEFAULT=ROOT/'results/feedback-revision-20261109'
OLD=ROOT/'analysis/article_packages/20261106T120036Z-7f9b932d0594'
PROTOCOLS=['20261105T231418Z-6562d0686dcf','20261106T002226Z-6a8673f9695a']

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):atomic_json(path,value)

def initialize(output):
    output.mkdir(parents=True,exist_ok=True)
    expected={'design':read(DESIGN),'design_sha256':sha(DESIGN),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'analysis/feedback_statistics.py',ROOT/'src/neutrinos/sim.py',ROOT/'src/neutrinos/study_analysis.py',ROOT/'scripts/run_correlation_search.py']},
        'ibm_jobs_submitted':0}
    path=output/'plan.json'
    if path.exists() and read(path)!=expected:raise ValueError('Plan changed; preserve this output and select a new --output')
    save(path,expected)

def capture(output):
    """Capture sufficient block moments plus raw initial labels; preserve huge original z arrays."""
    initialize(output);folder=output/'original_h1';folder.mkdir(exist_ok=True)
    archived={}
    for name in ['T03-classica-principal','T03-classica-extensao']:
        for c in read(OLD/f'reports/{name}.json')['cases']:archived[c['cell']['n'],c['cell']['mu']]=c
    records=[]
    for protocol in PROTOCOLS:
        root=ROOT/'results/protocols'/protocol
        record=read(root/'run.json');spec=read(root/'protocol.json');requests={s['id']:s['request'] for s in spec['steps']}
        groups={}
        for st in record['steps']:
            if st['status']!='completed':raise ValueError('Original run incomplete')
            req=requests[st['id']];cfg=req['config'];groups.setdefault((cfg['n'],cfg['mu']),[]).append((st,req))
        for (n,mu),items in sorted(groups.items()):
            name=f'n{n}_mu{mu:g}';target=folder/(name+'.npz');meta=folder/(name+'.json')
            if meta.exists():
                entry=read(meta)
                if sha(target)!=entry['arrays_sha256']:raise ValueError('Captured H1 data changed')
                records.append(entry);continue
            blocks={k:[] for k in ['m1','m2','m3']};seeds=[];labels=[];sources=[];references=None
            for st,req in items:
                run=ROOT/'results'/st['run_id'];version=(run/'current').read_text().strip();v=run/'versions'/version
                manifest=read(v/'manifest.json')
                if ExperimentConfig.from_dict(manifest['config_input'])!=ExperimentConfig.from_dict(req['config']):
                    raise ValueError('Physical configuration mismatch')
                with np.load(v/'moments.npz',allow_pickle=False) as a:
                    reference={k:a['exact_'+k].copy() for k in ['m1','c2','c3']}
                    if references is None:references=reference
                    for k in reference:np.testing.assert_allclose(reference[k],references[k],atol=1e-13,rtol=0)
                    for k in blocks:blocks[k].append(a['psa_'+k].copy())
                seed=req['config']['seed'];seeds.append(seed)
                signs=np.random.default_rng(seed).choice([-1.,1.],size=(req['trajectories'],n,2))
                raw=(((signs.reshape(req['trajectories'],2*n)+1)/2).astype(np.uint64)@(np.uint64(1)<<np.arange(2*n,dtype=np.uint64))).astype(np.uint32)
                labels.append(raw)
                sources.append({'run_id':st['run_id'],'version':version,'request':req,
                    'original_moments_sha256_recorded':read(v/'artifacts.json')['files']['moments.npz']['sha256']})
            if len(blocks['m1'])!=20 or len(set(seeds))!=20:raise ValueError('Expected 20 independent blocks')
            np.savez_compressed(target,**{k:np.stack(v) for k,v in blocks.items()},
                **{'reference_'+k:v for k,v in references.items()},raw_initial_labels=np.stack(labels),seeds=seeds,
                original_D_bootstrap=archived[n,mu]['psa_analysis']['r3_minus_r2_bootstrap'])
            entry={'id':name,'n':n,'mu':mu,'arrays':str(target.relative_to(output)),
                'arrays_sha256':sha(target),'blocks':20,'config':items[0][1]['config'],
                'sources':sources,'original_analysis':archived[n,mu]['psa_analysis'],
                'data_scope':'Float64 per-block uncentered moments sufficient for every H1 statistic; raw sampled sign-state labels and solver/seed/options permit trajectory regeneration. Full original sample_z arrays remain untouched locally; not duplicated in this package.'}
            save(meta,entry);records.append(entry);print('Captured',name,flush=True)
    checks=[]
    for p in sorted((OLD/'reports').glob('*.json')):
        data=read(p)
        if 'checks' in data:checks.append({'source':str(p.relative_to(ROOT)),'source_sha256':sha(p),'checks':data['checks']})
    save(output/'original_controls.json',checks)
    save(output/'original_h1.json',{'status':'captured','cases':records,'original_reports':'T03 principal and extension','original_results_changed':False})

def audit(output):
    initialize(output);result=[];folder=output/'h1_audit';folder.mkdir(exist_ok=True)
    for case in read(output/'original_h1.json')['cases']:
        target=folder/(case['id']+'.json')
        if target.exists():result.append(read(target));continue
        with np.load(output/case['arrays']) as a:
            blocks=[a[k] for k in ['m1','m2','m3']];ref2=a['reference_c2'];ref3=a['reference_c3']
            center,draws,jack=bootstrap_statistics(blocks,ref2,ref3,case['n'])
            difference=float(np.max(np.abs(draws[:,0]-a['original_D_bootstrap'])))
            if difference>1e-9:raise ValueError(f'Original bootstrap not reproduced: {case["id"]}: {difference}')
        path=folder/(case['id']+'.npz');np.savez_compressed(path,central=center,draws=draws,jackknife=jack)
        details={key:intervals(center[i],draws[:,i],jack[:,i]) for i,key in enumerate(['D','R3','R2'])}
        original=case['original_analysis'];old_ci=original['r3_minus_r2_ci95'];old_center=original['c3']['normalized_rmse']-original['c2']['normalized_rmse']
        record={'id':case['id'],'n':case['n'],'mu':case['mu'],'central_D_R3_R2':center.tolist(),
            'intervals':details,'original_outside_own_interval':not old_ci[0]<=old_center<=old_ci[1],
            'original_bootstrap_reconstruction_error':difference,
            'bootstrap_mean_bias_D':float(draws[:,0].mean()-center[0]),
            'arrays':str(path.relative_to(output)),'arrays_sha256':sha(path),
            'inference':'Sensitivity of original finite-MC estimate, not validated coverage at this N; do not use containment of the estimate to select a method.'}
        save(target,record);result.append(record);print('Audited',case['id'],flush=True)
    trends=[]
    for n in sorted({c['n'] for c in result}):
        cases=sorted([c for c in result if c['n']==n],key=lambda c:c['mu'])
        x=np.log10([c['mu'] for c in cases]);centers=[];draws=[];jack=[]
        for c in cases:
            with np.load(output/c['arrays']) as a:centers.append(a['central'][1]);draws.append(a['draws'][:,1]);jack.append(a['jackknife'][:,1])
        central=float(slope(x,np.array(centers)));b=slope(x,np.array(draws).T);j=slope(x,np.array(jack).T)
        trends.append({'n':n,'statistic':'OLS slope R3 vs log10(mu)','slope':central,'intervals':intervals(central,b,j),
            'pairing':'same original PSA seed labels across mu; preserve joint seed indices',
            'scope':'post-collection trend analysis; bootstrap coverage for nonlinear R3 not assumed'})
    save(output/'h1_audit.json',{'status':'reanalyzed_all_25_cells','cases':result,'R3_trends':trends,
        'original_anomalies':sum(c['original_outside_own_interval'] for c in result),
        'original_estimator_changed':False,'method_selected_automatically':False})

def coverage(output):
    initialize(output);design=read(DESIGN)['h1_audit']['coverage'];folder=output/'coverage';folder.mkdir(exist_ok=True);rows=[]
    for mu in design['mu']:
        target=folder/f'mu{mu:g}.json'
        if target.exists():rows.append(read(target));continue
        cfg=ExperimentConfig(n=4,mu=mu,t_max=10,points=201,flavors=(0,0,1,1))
        initial=initial_support(cfg,0,256);z=_evolve_spins(cfg,initial,24)[...,2]
        coarse=_from_trajectories(cfg,_evolve_spins(cfg,initial,12)[...,2],'coarse',{})
        population=_from_trajectories(cfg,z,'known finite population',{});exact=classical_exact(cfg)
        integration=float(np.max(np.abs(population.c3-coarse.c3)))
        if integration>1e-5:raise ValueError('Coverage population integration unresolved')
        feature=np.concatenate([z,np.prod(z[:,:,cfg.pair_index],axis=-1),np.prod(z[:,:,cfg.trio_index],axis=-1)],axis=-1).transpose(1,0,2)
        features=feature.reshape(256,-1);cuts=[4,10,14]
        truth=statistics([population.m1,population.m2,population.m3],exact.c2,exact.c3,4)[0]
        rng=np.random.default_rng(design['seed']+round(mu*100));records=[];estimates=[];bias=[]
        for campaign in range(design['campaigns']):
            weights=rng.multinomial(4096,np.ones(256)/256,size=20)/4096
            values=(weights@features).reshape(20,201,14)
            blocks=[values[:,:,:cuts[0]],values[:,:,cuts[0]:cuts[1]],values[:,:,cuts[1]:cuts[2]]]
            central,draws,jack=bootstrap_statistics(blocks,exact.c2,exact.c3,4,
                repetitions=design['bootstrap_repetitions'],seed=design['seed']+campaign+int(mu*10000))
            ci=intervals(central[0],draws[:,0],jack[:,0]);records.append(ci);estimates.append(float(central[0]));bias.append(float(draws[:,0].mean()-central[0]))
            if (campaign+1)%25==0:print(f'Coverage mu={mu}: {campaign+1}/{design["campaigns"]}',flush=True)
        methods={}
        for name in ['percentile','basic','BCa']:
            covered=int(sum(c[name] is not None and c[name][0]<=truth<=c[name][1] for c in records))
            methods[name]={'covered':covered,'total':len(records),'coverage':covered/len(records),'coverage_ci95':wilson(covered,len(records)),
                'mean_width':float(np.mean([c[name][1]-c[name][0] for c in records if c[name] is not None]))}
        payload={'n':4,'mu':mu,'true_D':float(truth),'integration_max_c3':integration,
            'methods':methods,'mean_estimator_bias':float(np.mean(estimates)-truth),'mean_bootstrap_bias':float(np.mean(bias)),
            'bca_unresolved_tail_count':sum(c['BCa_tail_below_resolution'] for c in records),
            'scope':'20x4096 iid draws from all 256 PSA initial configurations; N4 original time window only; no extrapolation to larger N',
            'campaign_intervals':records,'campaign_estimates':estimates}
        np.savez_compressed(folder/f'mu{mu:g}_population.npz',z=z,reference_m1=exact.m1,reference_c2=exact.c2,reference_c3=exact.c3)
        save(target,payload);rows.append(payload)
    save(output/'coverage.json',{'status':'completed','cases':rows,'methods_predeclared':['percentile','basic','BCa'],
        'interpretation':'An interval excluding its point estimate is not itself a coding error; inferential adequacy is judged against known population truth and coverage, within this validation scope.'})

def controlled_h1(output):
    initialize(output);design=read(DESIGN)['h1_controlled'];folder=output/'h1_controlled';folder.mkdir(exist_ok=True);rows=[]
    for n in design['n']:
        for mu in design['mu']:
            name=f'n{n}_mu{mu:g}';target=folder/(name+'.json')
            if target.exists():rows.append(read(target));continue
            cfg=search_config(n,mu,'domain','uniform');start=time.perf_counter()
            coarse=complete_psa(cfg,8);fine=complete_psa(cfg,16);exact=classical_exact(cfg)
            differences={k:float(np.max(np.abs(getattr(coarse,k)-getattr(fine,k)))) for k in ['pe','c2','c3']}
            if any(differences[k]>design['integration_limits'][k] for k in differences):
                save(folder/(name+'_failed_validation.json'),differences);raise ValueError('Controlled H1 integration failed: '+name)
            path=folder/(name+'.npz')
            np.savez_compressed(path,**{prefix+'_'+k:getattr(series,k) for prefix,series in [('exact',exact),('psa',fine),('coarse',coarse)] for k in ['m1','m2','m3']},times=cfg.times)
            fine_metrics={k:metrics(getattr(exact,k),getattr(fine,k)) for k in ['pe','c2','c3']}
            coarse_metrics={k:metrics(getattr(exact,k),getattr(coarse,k)) for k in ['pe','c2','c3']}
            row={'id':name,'n':n,'mu':mu,'config':cfg.record(),'support_size':4**n,
                'metrics':fine_metrics,'coarse_metrics':coarse_metrics,'integration_difference':differences,
                'D':fine_metrics['c3']['normalized_rmse']-fine_metrics['c2']['normalized_rmse'],
                'C3_zero_normalized_rmse':1.,'psa_beats_zero':fine_metrics['c3']['normalized_rmse']<1,
                'arrays':str(path.relative_to(output)),'arrays_sha256':sha(path),'elapsed_seconds':time.perf_counter()-start}
            save(target,row);rows.append(row);print('Controlled H1',name,f'{row["elapsed_seconds"]:.1f}s',flush=True)
    trends=[]
    for n in design['n']:
        cases=sorted([c for c in rows if c['n']==n],key=lambda c:c['mu']);x=np.log10([c['mu'] for c in cases])
        y=np.array([c['metrics']['c3']['normalized_rmse'] for c in cases]);yc=np.array([c['coarse_metrics']['c3']['normalized_rmse'] for c in cases])
        value=float(slope(x,y));bound=float(np.sum(np.abs(x-x.mean())*np.abs(y-yc))/np.sum((x-x.mean())**2))
        trends.append({'n':n,'statistic':'OLS slope R3 vs log10(mu)','slope':value,'observed_integration_sensitivity_bound':bound,
            'positive_beyond_observed_sensitivity':bool(value>bound),'adjacent_differences':np.diff(y).tolist(),'strictly_monotonic_on_grid':bool(np.all(np.diff(y)>0)),
            'scope':'deterministic finite grid; no sampling p-value, no generalization to other states/geometries/windows'})
    save(output/'h1_controlled.json',{'status':'completed','cases':rows,'trends':trends,'time_window':[0,3],
        'differs_from_original_T03_window':[0,10],'all_case_integration_checks_passed':True})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['capture','audit','coverage','h1'])
    parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args();{'capture':capture,'audit':audit,'coverage':coverage,'h1':controlled_h1}[args.stage](args.output.resolve())

if __name__=='__main__':main()
