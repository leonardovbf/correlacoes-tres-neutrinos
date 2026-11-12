#!/usr/bin/env python3
"""Reexecuta localmente programas IBM arquivados, sem chamadas à nuvem."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from ibm_quantum_schemas.executor.version_1_1 import ParamsModel
from qiskit import qpy
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.quantum_program.converters.converters_1_1 import quantum_program_from_1_1

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'analysis'),str(ROOT/'scripts'),str(ROOT/'src')]
from app.backend.audit import atomic_json
from run_correlation_noise import c3,marginal
from paired_aer_common import (compact_circuit,measurement_map,classical_probabilities,
    subset_properties,readout_response,calibrated_gate_model,initialization,
    asap_idle_relaxation,checked_density,strip_measurements)

DEFAULT=ROOT/'results/paired-aer-ibm-20261108'
MODELS=['ideal','readout_only','gates_relaxation','full_calibrated','full_asap_idle']


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def protocol():
    return {'status':'post_hardware_paired_validation','no_parameter_fitting':True,
        'input':'captured IBM QuantumProgram + original QPY + archived per-job properties',
        'execution':'same Samplex Pauli active-accum generator,32 variants/job,512 shots/variant N4;128 N6/N8',
        'shots':'same 20x16384,5x4096,5x4096 as IBM; raw counts; no readout inversion',
        'rng':'new local twirls seed240000+job_index; local measurements250000+10000*job_index+100*variant+model_index',
        'server_random_realizations':'not returned in archived options; replay matches generator/policy, not the identical server draw',
        'models':MODELS,'temperature_mK':0,'frequency_missing':'no thermal excitation assumed at T=0; no frequency fabricated',
        'full_calibrated':'Aer basic_device_gate_errors + T1/T2 during native gates + independent asymmetric readout + independent init_error X flips',
        'full_asap_idle':'same calibrated model with extra idle relaxation under assumed ASAP schedule from archived gate durations/barriers',
        'schedule_limitation':'actual hardware pulse schedule not archived; ASAP is sensitivity only',
        'bootstrap':'10000 independent job resamples for Aer and IBM; no double resampling of shots',
        'ideal_probability_limit':1e-5,'ideal_c3_limit':1e-5,'max_density_trace_deviation':1e-6,
        'numerical_control_amendment':'first Runtime template had1.39e-7 probability difference vs base QPY; preserve failed1e-9 check and validate C3 at the existing1e-5 numerical tolerance,0.1percent of equivalence margin. Do not resynthesize the captured program.',
        'comparison':'existing three physical points; no new candidate selection or new IBM jobs'}


def run(output):
    manifest=read(output/'capture_manifest.json')
    if manifest['status']!='captured' or len(manifest['jobs'])!=30:
        raise ValueError('Complete a captura dos 30 jobs existentes')
    expected={'protocol':protocol(),'capture_sha256':sha(output/'capture_manifest.json'),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'analysis/paired_aer_common.py']}}
    plan=output/'replay_plan.json'
    if plan.exists() and read(plan)!=expected:raise ValueError('Plano ou fontes mudaram; preserve os resultados antes de retomar')
    atomic_json(plan,expected)
    for index,entry in enumerate(manifest['jobs']):
        start=time.perf_counter();folder=output/entry['input_path'];job_folder=output/'replay'/entry['job_id']
        job_folder.mkdir(parents=True,exist_ok=True)
        marker=job_folder/'result.json'
        if marker.exists():
            prior=read(marker)
            if prior['replay_plan_sha256']!=sha(plan) or sha(job_folder/'arrays.npz')!=prior['arrays_sha256']:
                raise ValueError('Resultado de replay alterado')
            continue
        if any(sha(folder/name)!=value for name,value in entry['files_sha256'].items()):
            raise ValueError('Entradas do job foram alteradas')
        case=read(folder/'case.json');meta=read(folder/'metadata.json')
        with (folder/'base.qpy').open('rb') as stream:original=qpy.load(stream)[0]
        base,physical=compact_circuit(original);base_map=measurement_map(base)
        base_prob=classical_probabilities(Statevector.from_instruction(strip_measurements(base)).probabilities(),base_map)
        trios=list(combinations(range(case['n']),3))
        base_c3=np.array([c3(marginal(base_prob,trio)) for trio in trios])
        properties=subset_properties(read(folder/'calibration.json'),physical)
        response=readout_response(properties,base_map)
        noise,bp=calibrated_gate_model(properties,base)
        program,_=quantum_program_from_1_1(ParamsModel.model_validate_json((folder/'program.json').read_text()))
        item=program.items[0];item.samplex.finalize()
        sample=item.samplex.sample(item.samplex_arguments,num_randomizations=32,rng=240000+index,max_workers=2)
        if set(sample)!=set(['parameter_values']):
            raise ValueError('Saídas adicionais do Samplex exigem processamento explícito')
        params=sample['parameter_values'];shots=program.shots
        if shots*32!=case['shots'] or meta['num_randomizations']!=32:
            raise ValueError('Orçamento e randomizações não conferem')
        template,template_physical=compact_circuit(item.circuit,physical)
        if template_physical!=physical or measurement_map(template)!=base_map:
            raise ValueError('O programa alterou o mapeamento de leitura')
        with (job_folder/'compact_template.qpy').open('wb') as stream:qpy.dump(template,stream)
        simulator=AerSimulator(method='density_matrix',noise_model=noise,max_parallel_threads=2)
        probabilities=np.empty((len(MODELS),32,1<<case['n']));counts=np.empty_like(probabilities,dtype=np.int64)
        max_probability_error=0.;max_c3_error=0.;max_trace_error=0.;schedules=[]
        for variant in range(32):
            bound=template.assign_parameters(params[variant]);native=strip_measurements(bound)
            ideal=classical_probabilities(Statevector.from_instruction(native).probabilities(),base_map)
            error=float(np.max(np.abs(ideal-base_prob)));max_probability_error=max(max_probability_error,error)
            c3_error=float(np.max(np.abs(np.array([c3(marginal(ideal,trio)) for trio in trios])-base_c3)))
            max_c3_error=max(max_c3_error,c3_error)
            if error>1e-5 or c3_error>1e-5:raise ValueError(f'Falha de equivalência ideal do twirling: p={error},C3={c3_error}')
            # Um circuito base já compilado e um programa nativo: nenhuma chamada a transpile.
            full=initialization(native,properties)
            scheduled,schedule=asap_idle_relaxation(native,properties,bp)
            with_idle=initialization(scheduled,properties);schedules.append(schedule)
            circuits=[native.copy(),full,with_idle]
            for circuit in circuits:circuit.save_density_matrix()
            simulated=simulator.run(circuits,shots=1).result()
            if not simulated.success:raise ValueError('Aer não concluiu as matrizes densidade')
            quantum=[]
            for k in range(3):
                p,trace_error=checked_density(np.diag(np.asarray(simulated.data(k)['density_matrix'])).real)
                max_trace_error=max(max_trace_error,trace_error)
                quantum.append(classical_probabilities(p,base_map))
            values=[ideal,response@ideal,quantum[0],response@quantum[1],response@quantum[2]]
            for model,value in enumerate(values):
                value,_=checked_density(value);probabilities[model,variant]=value
                rng=np.random.default_rng(250000+10000*index+100*variant+model)
                counts[model,variant]=rng.multinomial(shots,value)
            if (variant+1)%8==0:
                print(f'N{case["n"]} job {index+1}/30: {variant+1}/32 variantes',flush=True)
        np.savez_compressed(job_folder/'arrays.npz',parameter_values=params,
            probabilities=probabilities,counts=counts,base_probabilities=base_prob,readout_matrix=response)
        if any(row.sum()!=case['shots'] for row in counts.sum(axis=1)):
            raise ValueError('Shots simulados não correspondem aos shots IBM')
        summary={'job_id':case['job_id'],'n':case['n'],'models':MODELS,'shots':case['shots'],
            'num_randomizations':32,'shots_per_randomization':shots,'physical_to_compact':physical,
            'compact_measurement_map':base_map,'original_qpy_sha256':entry['files_sha256']['base.qpy'],
            'template_gate_counts':dict(template.count_ops()),'original_gate_counts':dict(base.count_ops()),
            'max_ideal_probability_error':max_probability_error,'max_ideal_c3_error':max_c3_error,'max_trace_error':max_trace_error,
            'schedule_sensitivity':schedules,'elapsed_seconds':time.perf_counter()-start,
            'replay_plan_sha256':sha(plan),'arrays_sha256':sha(job_folder/'arrays.npz'),
            'template_sha256':sha(job_folder/'compact_template.qpy')}
        atomic_json(marker,summary)
        print(f'Concluído N{case["n"]} {index+1}/30 em {summary["elapsed_seconds"]:.1f}s',flush=True)
    analyze(output)


def analyze(output):
    entries=read(output/'capture_manifest.json')['jobs'];by_n={}
    for entry in entries:
        folder=output/entry['input_path'];case=read(folder/'case.json');job=output/'replay'/entry['job_id']
        summary=read(job/'result.json')
        if sha(job/'arrays.npz')!=summary['arrays_sha256']:raise ValueError('Arrays de replay alterados')
        with np.load(job/'arrays.npz') as arrays:
            simulated=arrays['counts'].sum(axis=1);expected=arrays['probabilities'].mean(axis=1)
        by_n.setdefault(entry['n'],[]).append({'case':case,'counts':simulated,'expected':expected,'ibm':np.array(case['counts'])})
    result={'status':'paired_replay_complete','ibm_jobs_submitted':0,'models':MODELS,
        'plan_sha256':sha(output/'replay_plan.json'),'comparisons':[]}
    for n,blocks in sorted(by_n.items()):
        case=blocks[0]['case'];trio=case['trio'];exact=case['reference']['exact'];psa=case['reference']['psa_protocol']
        hardware=np.stack([b['ibm'] for b in blocks]);ibm_total=hardware.sum(axis=0)
        ibm_value=float(c3(marginal(ibm_total/ibm_total.sum(),trio)))
        for m,label in enumerate(MODELS):
            aer=np.stack([b['counts'][m] for b in blocks]);total=aer.sum(axis=0)
            mean_p=np.mean([b['expected'][m] for b in blocks],axis=0)
            value=float(c3(marginal(total/total.sum(),trio)));expected=float(c3(marginal(mean_p,trio)))
            rng=np.random.default_rng(280000+n*100+m)
            wa=rng.multinomial(len(blocks),np.ones(len(blocks))/len(blocks),size=10000)
            wb=rng.multinomial(len(blocks),np.ones(len(blocks))/len(blocks),size=10000)
            # Cada linha preserva todos os bits e a correlação entre momentos.
            ma=np.stack([marginal(row,trio) for row in aer]);mb=np.stack([marginal(row,trio) for row in hardware])
            sa=wa@ma;sb=wb@mb;draw_a=c3(sa/sa.sum(axis=1,keepdims=True));draw_b=c3(sb/sb.sum(axis=1,keepdims=True))
            difference=draw_b-draw_a
            result['comparisons'].append({'n':n,'model':label,'jobs':len(blocks),'shots_per_environment':int(total.sum()),
                'trio':trio,'exact':exact,'psa':psa,'aer':value,'aer_expected':expected,'ibm':ibm_value,
                'aer_ci95_job_blocks':np.quantile(draw_a,[.025,.975]).tolist(),
                'ibm_ci95_job_blocks':np.quantile(draw_b,[.025,.975]).tolist(),
                'ibm_minus_aer':ibm_value-value,'ibm_minus_aer_ci95':np.quantile(difference,[.025,.975]).tolist(),
                'aer_absolute_error':abs(value-exact),'ibm_absolute_error':abs(ibm_value-exact),
                'aer_reduction_vs_psa_percent':100*(1-abs(value-exact)/abs(psa-exact)),
                'ibm_reduction_vs_psa_percent':100*(1-abs(ibm_value-exact)/abs(psa-exact))})
    atomic_json(output/'analysis.json',result)
    with (output/'comparison.csv').open('w') as stream:
        names=[key for key in result['comparisons'][0] if not key.endswith('ci95') and not key.endswith('job_blocks')]
        writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
        for row in result['comparisons']:writer.writerow({key:row[key] for key in names})
    print(output/'analysis.json',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT)
    args=parser.parse_args();run(args.output.resolve())
