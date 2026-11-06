#!/usr/bin/env python3
"""Extrai prévia descritiva e reavalia controles sem modificar a coleta ativa.

Registra código, revisões de origem, hashes e o nome usado no encaminhamento.
Não calcula IC95 nem confirma H1/H2; não altera relatórios/estados oficiais.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from app.backend import audit,protocol,service,study
from app.backend.storage import RunStore
from neutrinos.study_analysis import metrics,pooled


def dispatch_spec(spec):
    """Encaminha o nome público T03-classica-principal à análise 03_classica_principal."""
    mapping={protocol.read_protocol(ROOT/f'configs/protocols/artigo_v1/{stem}.json').name:stem for stem in study.ORDER}
    if spec.name not in mapping:
        raise ValueError(f'Fase oficial desconhecida: {spec.name}')
    return spec.model_copy(update={'name':mapping[spec.name]})


def preview(study_path, *, output=None, progress=print):
    root=service.store.root.resolve()
    study_path=study_path.resolve()
    state=json.loads(study_path.read_text())
    if study_path.parents[2]!=root or state['profile']!='official-v1-r2':
        raise ValueError('Use estudo oficial e o mesmo --output')
    if audit.environment_differences(state['environment']):
        raise ValueError('Use o mesmo snapshot do estudo; fontes/dependências mudaram')
    destination=output or root/'previews'/audit.new_id()
    destination.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,destination/'preview_results.py')
    report={'schema_version':1,'status':'running','purpose':'prévia descritiva de dados coletados',
        'started_utc':audit.utc_now(),'study_record':str(study_path),'study_status_at_read':state['status'],
        'study_record_sha256_at_read':audit.file_hash(study_path),'environment':audit.environment(),
        'source_snapshot':state['source_snapshot'],'analysis_script_sha256':audit.file_hash(Path(__file__)),
        'inference':'Sem IC95/Holm. Não confirma H1/H2. Resultados sujeitos à validação dos controles.',
        'phase_dispatch_issue':'Nomes públicos Txx-... não correspondiam aos nomes 0x_... esperados nas análises específicas; relatórios antigos continham só controles gerais.',
        'recovered_controls':[],'classical_cases':[],'artifacts':[]}
    record=destination/'preview.json'
    audit.atomic_json(record,report)
    try:
        for phase in state['phases']:
            if not phase.get('protocol_record') or phase['status']=='pending':
                continue
            path=Path(phase['protocol_record']);run=json.loads(path.read_text())
            spec=protocol.read_protocol(path.parent/'protocol.json')
            adapted=dispatch_spec(spec)
            if phase['status']=='completed' and phase['name'] in (
                'T00-reproducao-publicada','T01-controles','T02-integracao','T02-amostragem','T04-trotter','T04-qiskit'):
                progress('Reavaliando controles: '+phase['name'])
                analysis=study.analyze_phase(root,adapted,run,repetitions=2000)
                analysis.update(phase=spec.name,analysis_dispatch_name=adapted.name,
                    source_protocol_record=str(path),source_protocol_record_sha256=audit.file_hash(path))
                file=destination/(spec.name+'.json');audit.atomic_json(file,analysis)
                report['artifacts'].append({'path':file.name,'sha256':audit.file_hash(file)})
                failed=[c for c in analysis['checks'] if not c['pass']]
                report['recovered_controls'].append({'phase':spec.name,'status':analysis['status'],
                    'checks':len(analysis['checks']),'cases':len(analysis.get('cases',[])),
                    'failed':failed,'report_path':file.name})
                audit.atomic_json(record,report)
            if phase['name'] not in ('T03-classica-principal','T03-classica-extensao'):
                continue
            groups={}
            for step,step_state in zip(spec.steps,run['steps'],strict=True):
                if step.action!='classical' or step_state['status']!='completed':
                    continue
                cfg=step.request['config'];key=study._cell(cfg)
                groups.setdefault(key,[]).append((step,step_state))
            for key,items in groups.items():
                if len(items)!=20:
                    report.setdefault('incomplete_cells',[]).append({'phase':phase['name'],'cell':json.loads(key),'completed_seeds':len(items),'expected_seeds':20})
                    continue
                cell=json.loads(key);progress(f'Prévia: N={cell["n"]}, μ={cell["mu"]}, 20 sementes')
                blocks=[];sources=[];reference=None
                for step,step_state in items:
                    execution,artifacts,_=study._load(root,step_state)
                    arrays=study._arrays(artifacts,('psa_m','exact_pe','exact_c2','exact_c3'))
                    blocks.append({field:arrays['psa_'+field] for field in ('m1','m2','m3')})
                    if reference is None:
                        reference=arrays
                    sources.append({'execution_id':execution['execution_id'],'seed':step.request['config']['seed'],
                        'revision':execution['revision_after'],'run_id':step_state['run_id'],
                        'moments':next(a for a in execution['artifacts'] if a['path'].endswith('/moments.npz'))})
                c2,c3=pooled(blocks,cell['n']);pe=(1+np.mean([b['m1'] for b in blocks],axis=0))/2
                value={'phase':phase['name'],'cell':cell,'seed_blocks':20,'trajectories_per_block':4096,
                    'total_trajectories':81920,'pe':metrics(reference['exact_pe'],pe),
                    'c2':metrics(reference['exact_c2'],c2),'c3':metrics(reference['exact_c3'],c3),
                    'sources':sources}
                report['classical_cases'].append(value)
                prefix=f'N{cell["n"]}_mu{cell["mu"]}'
                data=destination/(prefix+'.csv')
                with data.open('w') as f:
                    writer=csv.writer(f);writer.writerow(['tau','trio_index','exact_c3','psa_c3'])
                    times=np.linspace(0,cell['t_max'],cell['points'])
                    for t,tau in enumerate(times):
                        for k in range(c3.shape[1]):
                            writer.writerow([tau,k,reference['exact_c3'][t,k],c3[t,k]])
                report['artifacts'].append({'path':data.name,'sha256':audit.file_hash(data)})
                if cell['n']==4 and cell['mu']==3.:
                    os.environ.setdefault('MPLCONFIGDIR',str(root/'_cache'/'matplotlib'))
                    os.environ.setdefault('XDG_CACHE_HOME',str(root/'_cache'/'fonts'))
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
                    fig.suptitle('PRÉVIA DESCRITIVA — N=4, μ=3; 20 × 4.096 trajetórias; sem IC')
                    axes[0].plot(times,reference['exact_c3'][:,0],color='black',label='Exato')
                    axes[0].plot(times,c3[:,0],'--',color='tab:blue',label='PSA')
                    axes[0].set(xlabel='τ',ylabel='Kzzz do trio (0,1,2)');axes[0].legend()
                    axes[1].plot(times,np.sqrt(np.mean((c3-reference['exact_c3'])**2,axis=1)),color='tab:blue')
                    axes[1].set(xlabel='τ',ylabel='RMSE de Kzzz entre os trios')
                    png=destination/'previa_N4_mu3.png';fig.savefig(png,dpi=180);plt.close(fig)
                    report['artifacts'].append({'path':png.name,'sha256':audit.file_hash(png)})
                audit.atomic_json(record,report)
        report['status']='descriptive_preview_ready'
        report['scientific_controls_status']='failed' if any(c['status']=='failed' for c in report['recovered_controls']) else 'passed'
        summary=destination/'summary.csv'
        with summary.open('w') as f:
            writer=csv.writer(f);writer.writerow(['N','mu','E_pe','E_c2','E_c3','S_c2','S_c3','R2','R3'])
            for c in report['classical_cases']:
                writer.writerow([c['cell']['n'],c['cell']['mu'],c['pe']['rmse'],c['c2']['rmse'],c['c3']['rmse'],
                    c['c2']['signal_rms'],c['c3']['signal_rms'],c['c2']['normalized_rmse'],c['c3']['normalized_rmse']])
        report['artifacts'].append({'path':summary.name,'sha256':audit.file_hash(summary)})
    except BaseException as exc:
        report.update(status='failed',error=audit.safe_error(exc));raise
    finally:
        report['finished_utc']=audit.utc_now();audit.atomic_json(record,report)
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    args=parser.parse_args();service.store=RunStore(args.output.resolve())
    print(preview(args.study),flush=True)
