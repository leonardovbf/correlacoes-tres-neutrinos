#!/usr/bin/env python3
"""Fixed-circuit H2 noise sweep, calibrated measurement budgets, no cloud access."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from qiskit import qpy
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel,depolarizing_error
from ibm_quantum_schemas.executor.version_1_1 import ParamsModel
from qiskit_ibm_runtime.quantum_program.converters.converters_1_1 import quantum_program_from_1_1

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'analysis'),str(ROOT/'scripts')]
from run_feedback_revision import initialize,read,save,sha,DEFAULT,DESIGN
from paired_aer_common import compact_circuit,measurement_map,strip_measurements,classical_probabilities,checked_density
from run_correlation_noise import c3,response
from feedback_statistics import first_loss,wilson


def assignment(n,p):
    states=np.arange(1<<n);distance=np.zeros((1<<n,1<<n),dtype=int)
    for q in range(n):distance+=((states[:,None]>>q)&1)!=((states[None,:]>>q)&1)
    return p**distance*(1-p)**(n-distance)


def trio(values):
    # The fixed principal trio is bits 0,1,2; sum over spectator bit 3.
    values=np.asarray(values)
    if values.shape[-1]!=16:raise ValueError('Expected four measured bits')
    return values.reshape(*values.shape[:-1],2,8).sum(axis=-2)


def sample_counts(probabilities,readout,rng):
    matrix=assignment(4,readout);observed=probabilities@matrix.T
    return {'raw':rng.multinomial(10240,observed,size=(32,)),
        'signal':rng.multinomial(7680,observed,size=(32,)),
        'zero':rng.multinomial(40960,matrix[:,0]),'one':rng.multinomial(40960,matrix[:,-1])}


def analyze_counts(counts,exact,psa,seed,repetitions=2000):
    rng=np.random.default_rng(seed)
    nraw=int(counts['raw'].sum());nsig=int(counts['signal'].sum())
    if nraw!=327680 or nsig+counts['zero'].sum()+counts['one'].sum()!=nraw:
        raise ValueError('Unequal total measurement budgets')
    calibration=response(trio(counts['zero']),trio(counts['one']))
    observed=trio(counts['signal'].sum(axis=0))/nsig
    corrected=np.linalg.solve(calibration[0],observed)
    central=[float(c3(trio(counts['raw'].sum(axis=0))/nraw)),float(c3(corrected))]
    raw=rng.multinomial(10240,counts['raw']/10240,size=(repetitions,32)).sum(axis=1)
    signal=rng.multinomial(7680,counts['signal']/7680,size=(repetitions,32)).sum(axis=1)
    zero=rng.multinomial(40960,counts['zero']/40960,size=repetitions)
    one=rng.multinomial(40960,counts['one']/40960,size=repetitions)
    matrices=response(trio(zero),trio(one));condition=float(np.max(np.linalg.cond(matrices)))
    if not np.isfinite(condition) or condition>10:raise ValueError('Unresolved calibration, no selective replica deletion')
    corrected=np.linalg.solve(matrices,(trio(signal)/nsig)[...,None])[...,0]
    draws=np.stack((c3(trio(raw)/nraw),c3(corrected)),axis=-1)
    result={}
    for i,method in enumerate(['raw','mitigated']):
        difference=np.quantile(draws[:,i]-exact,[.025,.975])+np.array([-1e-8,1e-8])
        advantage={}
        for label,reference in [('PSA',psa),('zero',0.)]:
            delta=np.abs(draws[:,i]-exact)-abs(reference-exact)
            ci=np.quantile(delta,[.025,.975])+np.array([-1e-5,1e-5])
            advantage[label]={'difference':abs(central[i]-exact)-abs(reference-exact),'ci95':ci.tolist(),'upper_below_zero':bool(ci[1]<0)}
        result[method]={'estimate':central[i],'difference_exact_ci95':difference.tolist(),
            'primary_equivalent':bool(difference[0]>=-.01 and difference[1]<=.01),
            'advantages':advantage,'secondary_better_than_both':all(v['upper_below_zero'] for v in advantage.values())}
    return result,draws,condition


class Experiment:
    def __init__(self,output):
        initialize(output);self.output=output;self.folder=output/'h2';self.folder.mkdir(exist_ok=True)
        self.design=read(DESIGN)['h2']
        capture=ROOT/'results/paired-aer-ibm-20261108'
        manifest=read(capture/'capture_manifest.json');entry=next(e for e in manifest['jobs'] if e['n']==4)
        original=capture/entry['input_path'];local=self.folder/'input';local.mkdir(exist_ok=True)
        for name in ['base.qpy','program.json','case.json','metadata.json']:
            source=original/name;target=local/name
            if sha(source)!=entry['files_sha256'][name]:raise ValueError('Archived IBM input changed')
            if target.exists() and sha(target)!=sha(source):raise ValueError('Local input changed')
            if not target.exists():shutil.copy2(source,target)
        identity={'design_sha256':sha(DESIGN),'script_sha256':sha(Path(__file__)),
            'helper_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'analysis/paired_aer_common.py',ROOT/'scripts/run_correlation_noise.py',ROOT/'analysis/feedback_statistics.py']},
            'inputs_sha256':{p.name:sha(p) for p in local.iterdir()},'ibm_jobs_submitted':0,
            'sampling':'fixed 32 twirl strata with equal shots; stratified signal bootstrap and independently reestimated calibration',
            'bootstrap_reference_bound':1e-8,'PSA_numerical_bound':1e-5}
        path=self.folder/'plan.json'
        if path.exists() and read(path)!=identity:raise ValueError('H2 sources changed; preserve this attempt')
        save(path,identity)
        case=read(local/'case.json');self.exact=case['reference']['exact'];self.psa=case['reference']['psa_full_support']
        with (local/'base.qpy').open('rb') as f:base=qpy.load(f)[0]
        base,physical=compact_circuit(base);mapping=measurement_map(base)
        expected=classical_probabilities(Statevector.from_instruction(strip_measurements(base)).probabilities(),mapping)
        program,_=quantum_program_from_1_1(ParamsModel.model_validate_json((local/'program.json').read_text()))
        item=program.items[0];item.samplex.finalize()
        params=item.samplex.sample(item.samplex_arguments,num_randomizations=32,rng=920000,max_workers=2)['parameter_values']
        template,_=compact_circuit(item.circuit,physical)
        if measurement_map(template)!=mapping:raise ValueError('Measurement mapping changed')
        self.native=[];self.ideal=[]
        for p in params:
            circuit=strip_measurements(template.assign_parameters(p));self.native.append(circuit)
            ideal=classical_probabilities(Statevector.from_instruction(circuit).probabilities(),mapping)
            if np.max(np.abs(ideal-expected))>1e-5:raise ValueError('Twirling failed equivalence')
            self.ideal.append(ideal)
        self.ideal=np.array(self.ideal);self.mapping=mapping
        self.context={'case':case,'physical_to_compact':physical,'measurement_map':mapping,
            'base_ops':dict(base.count_ops()),'template_ops':dict(template.count_ops()),
            'ideal_c3':float(c3(trio(self.ideal.mean(axis=0)))),
            'ideal_absolute_error':float(abs(c3(trio(self.ideal.mean(axis=0)))-self.exact)),
            'max_probability_equivalence_error':float(np.max(np.abs(self.ideal-expected)))}
        save(self.folder/'context.json',self.context)
        with (self.folder/'template.qpy').open('wb') as stream:qpy.dump(template,stream)
        np.savez_compressed(self.folder/'twirls.npz',parameter_values=params,ideal_probabilities=self.ideal)

    def probabilities(self,p1,p2):
        folder=self.folder/'probabilities';folder.mkdir(exist_ok=True)
        path=folder/f'p1_{p1:.12g}_p2_{p2:.12g}.npz'
        if path.exists():
            with np.load(path) as a:return a['probabilities']
        if p1==p2==0:values=self.ideal
        else:
            noise=NoiseModel(basis_gates=['rz','sx','x','cz'])
            if p1:noise.add_all_qubit_quantum_error(depolarizing_error(p1,1),['sx','x'])
            if p2:noise.add_all_qubit_quantum_error(depolarizing_error(p2,2),['cz'])
            simulator=AerSimulator(method='density_matrix',noise_model=noise,max_parallel_threads=2)
            circuits=[c.copy() for c in self.native]
            for c in circuits:c.save_density_matrix()
            result=simulator.run(circuits,shots=1).result()
            if not result.success:raise ValueError('Aer failed')
            values=[]
            for i in range(32):
                diagonal,_=checked_density(np.diag(np.asarray(result.data(i)['density_matrix'])).real)
                values.append(classical_probabilities(diagonal,self.mapping))
            values=np.array(values)
        np.savez_compressed(path,probabilities=values);return values

    def expected(self,p1,p2,readout):
        probabilities=self.probabilities(p1,p2).mean(axis=0)
        return [float(c3(trio(assignment(4,readout)@probabilities))),float(c3(trio(probabilities)))]

    def family_parameters(self,family,level):
        if family=='readout':return 0.,0.,level
        return (1e-4 if family=='two_qubit_with_p1' else 0.),level,(0. if family=='two_qubit_no_readout' else .03)

    def levels(self,family):
        initial=self.design['readout'] if family=='readout' else self.design['p2']
        levels=set(initial);changes=[]
        values={p:self.expected(*self.family_parameters(family,p)) for p in initial}
        for method in range(2):
            for lo,hi in zip(initial[:-1],initial[1:]):
                def successful(p):return abs(self.expected(*self.family_parameters(family,p))[method]-self.exact)<=.01
                if successful(lo)==successful(hi):continue
                a,b=lo,hi
                for _ in range(3):
                    mid=(a+b)/2;levels.add(mid)
                    if successful(mid)==successful(a):a=mid
                    else:b=mid
                changes.append({'method':['raw','mitigated'][method],'initial_bracket':[lo,hi],'refined_bracket':[a,b]})
        return sorted(levels),changes

    def run(self):
        rows=[];refinements={}
        for family in self.design['families']:
            levels,refinements[family]=self.levels(family)
            for level in levels:
                p1,p2,readout=self.family_parameters(family,level)
                key=f'{family}_{level:.12g}';folder=self.folder/'rows'/key;folder.mkdir(parents=True,exist_ok=True)
                path=folder/'result.json'
                if path.exists():rows.append(read(path));continue
                probabilities=self.probabilities(p1,p2)
                seed=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)
                counts=sample_counts(probabilities,readout,np.random.default_rng(seed))
                result,draws,condition=analyze_counts(counts,self.exact,self.psa,seed+1)
                power=[];power_counts={k:[] for k in counts};power_intervals=[]
                for campaign in range(self.design['decision_campaigns']):
                    new=sample_counts(probabilities,readout,np.random.default_rng(seed+100+campaign))
                    decision,_,_=analyze_counts(new,self.exact,self.psa,seed+10000+campaign,
                        repetitions=self.design['probability_interval_repetitions'])
                    power.append([decision[m]['primary_equivalent'] for m in ['raw','mitigated']])
                    power_intervals.append([decision[m]['difference_exact_ci95'] for m in ['raw','mitigated']])
                    for k,v in new.items():power_counts[k].append(v)
                power=np.asarray(power,dtype=bool);analytic=self.expected(p1,p2,readout)
                power_summary={}
                for i,method in enumerate(['raw','mitigated']):
                    successes=int(power[:,i].sum());power_summary[method]={'successes':successes,'campaigns':len(power),
                        'probability':successes/len(power),'ci95':wilson(successes,len(power))}
                lowraw,highraw=wilson(int(power[:,0].sum()),len(power),confidence=.975)
                lowmit,highmit=wilson(int(power[:,1].sum()),len(power),confidence=.975)
                arrays=folder/'counts.npz'
                np.savez_compressed(arrays,**counts,bootstrap_values=draws,power_success=power,
                    power_intervals=power_intervals,**{'power_'+k:np.array(v) for k,v in power_counts.items()})
                record={'id':key,'family':family,'level':level,'p1':p1,'p2':p2,'readout':readout,'seed':seed,
                    'expected_c3':dict(zip(['raw','mitigated'],analytic)),
                    'expected_equivalent':{m:bool(abs(analytic[i]-self.exact)<=.01) for i,m in enumerate(['raw','mitigated'])},
                    'observed':result,'decision_probability':power_summary,
                    'mitigated_minus_raw_decision_probability':{'estimate':power_summary['mitigated']['probability']-power_summary['raw']['probability'],
                        'conservative_ci95':[lowmit-highraw,highmit-lowraw]},
                    'max_calibration_condition':condition,'arrays':str(arrays.relative_to(self.output)),'arrays_sha256':sha(arrays),
                    'shots_per_method':327680,'ideal_discretization_bias_is_not_removed':True}
                save(path,record);rows.append(record)
                print(f'H2 {key}: P(equivalência) bruto={power_summary["raw"]["probability"]:.2f}, mitigado={power_summary["mitigated"]["probability"]:.2f}',flush=True)
        thresholds=[]
        for family in self.design['families']:
            values=sorted([r for r in rows if r['family']==family],key=lambda r:r['level'])
            levels=[r['level'] for r in values];entry={'family':family,'methods':{}}
            for method in ['raw','mitigated']:
                entry['methods'][method]={'expected':first_loss(levels,[r['expected_equivalent'][method] for r in values]),
                    'finite_shot_single_campaign':first_loss(levels,[r['observed'][method]['primary_equivalent'] for r in values]),
                    'interpretation':'grid brackets, not confidence intervals for threshold; decision probabilities have separate Monte Carlo uncertainty'}
            thresholds.append(entry)
        save(self.output/'h2.json',{'status':'completed','context':self.context,'rows':rows,'thresholds':thresholds,
            'refinement_log':refinements,'ibm_jobs_submitted':0,'scientific_scope':'fixed-circuit local noise-family characterization; pointwise intervals; independent confirmation required for general claims'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args();Experiment(args.output.resolve()).run()
