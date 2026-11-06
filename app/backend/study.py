"""Coleta do artigo: preflight, controles, retomada e análise de revisões imutáveis."""
from __future__ import annotations
import csv
import json
import os
import shutil
import sys
from pathlib import Path
import numpy as np
from neutrinos.sim import ExperimentConfig
from neutrinos.study_analysis import connected, h1, h2, independent_exact_check, metrics, pooled
from . import audit, protocol, service
from .storage import ROOT

ORDER = ['00_reproducao_publicada','01_controles','02_integracao','02_amostragem',
         '04_trotter','04_qiskit','03_classica_principal','03_classica_extensao',
         '05_medicoes','06_ruido','07_mitigacao']
BENCHMARK = ROOT/'data/benchmarks/lacroix2024'


def phase_key(name):
    """Aceita o nome público do protocolo e o identificador usado no smoke."""
    name=name.removeprefix('smoke-')
    aliases={f'T{stem[:2]}-{stem[3:].replace("_", "-")}':stem for stem in ORDER}
    aliases['T02-amostragem-suplementar']='02_amostragem_suplementar'
    return aliases.get(name,name)


def official_specs(extension=True):
    return [protocol.read_protocol(ROOT/f'configs/protocols/artigo_v1/{name}.json')
            for name in ORDER if extension or name!='03_classica_extensao']


def smoke_specs():
    """Perfil de teste do software, separado do protocolo confirmatório."""
    def ref(identifier, *, mu=3., seed=1, substeps=12, trajectories=64):
        return {'id':identifier,'action':'classical','request':{'config':{
            'n':4,'mu':mu,'theta':.2,'t_max':2.,'points':8,'seed':seed,
            'flavors':[0,0,1,1],'omega_values':[.7,.9,1.1,1.3]},
            'trajectories':trajectories,'substeps':substeps}}
    specs=[]
    for name in ORDER:
        steps=[]
        if name=='00_reproducao_publicada':
            steps=[ref('software_only')]
        elif name=='01_controles':
            steps=[ref('control',mu=0),{'id':'circuit','action':'circuit','run_from':'control','request':{'steps':16,'interval_index':7}}]
        elif name=='02_integracao':
            steps=[ref(f's{seed}_h{h}',seed=seed,substeps=h) for seed in range(1,4) for h in (8,12)]
        elif name=='02_amostragem':
            steps=[ref(f's{seed}_m{m}',seed=seed,trajectories=m) for seed in range(1,4) for m in (32,64)]
        elif name in ('03_classica_principal','03_classica_extensao'):
            steps=[ref(f's{seed}',seed=seed) for seed in range(10001,10004)]
        elif name=='04_trotter':
            steps=[ref('r')]+[{'id':f'q{h}','action':'quantum','run_from':'r','request':{'steps':h,'shots':32,'readout_error':0}} for h in (1,16)]
        elif name=='04_qiskit':
            steps=[ref('r'),{'id':'verify','action':'circuit','run_from':'r','request':{'steps':16,'interval_index':7}}]
        else:
            for seed in range(40001,40004):
                parent=f's{seed}'
                steps.extend([ref(parent,seed=seed),{'id':f'{parent}_ideal','action':'quantum','run_from':parent,'request':{'steps':16,'shots':256,'readout_error':0}}])
                if name in ('06_ruido','07_mitigacao'):
                    steps.append({'id':f'{parent}_counts','action':'mitigation' if name=='07_mitigacao' else 'aer',
                        'run_from':parent,'request':{'interval_index':7,'steps':16,'shots':256,'kind':'c3','index':0,
                            'single_qubit_error':.001,'two_qubit_error':.01,'readout_error':.03}})
        specs.append(protocol.ProtocolSpec(name='smoke-'+name,description='Validação de software; não usar no artigo.',steps=steps))
    return specs


def preflight(*, smoke=False, extension=True, specs=None):
    from importlib.metadata import version, PackageNotFoundError
    import platform
    import psutil
    specs=specs if specs is not None else (smoke_specs() if smoke else official_specs(extension))
    differences=[]
    for line in (ROOT/'requirements-research.lock').read_text().splitlines():
        if '==' not in line or line.startswith('#'):
            continue
        name,expected=line.split('==')
        try:
            actual=version(name)
        except PackageNotFoundError:
            actual=None
        if actual!=expected:
            differences.append({'package':name,'expected':expected,'actual':actual})
    if platform.python_version()!='3.14.3':
        differences.append({'package':'python','expected':'3.14.3','actual':platform.python_version()})
    source=json.loads((BENCHMARK/'source.json').read_text())
    if audit.file_hash(BENCHMARK/'figure2c.csv')!=source['csv_sha256']:
        raise ValueError('Referência publicada alterada; extraia e versione novamente')
    root=service.store.root
    root.mkdir(parents=True,exist_ok=True)
    # Limite superior conservador sem contar compressão: cada revisão recontém as amostras PSA.
    total=0
    peak=0
    for spec in specs:
        refs={}
        for step in spec.steps:
            if step.action=='classical':
                cfg=step.request['config']; ExperimentConfig.from_dict(cfg)
                m=step.request['trajectories']; n=cfg['n']; t=cfg['points']
                size=8*t*m*n
                refs[step.id]=size
                total+=size
                peak=max(peak,16*t*(1<<n)+size+8*t*256*n*3*4)
            elif step.run_from:
                total+=refs.get(step.run_from,0)
    # JSONs, índices de momentos, fontes, arquivos temporários e margens explícitas.
    estimated_disk=int(total*1.5+512*1024**2)
    estimated_ram=int(peak*3+512*1024**2)
    disk=shutil.disk_usage(root).free
    ram=psutil.virtual_memory().available
    checks=independent_exact_check()
    return {'schema_version':1,'profile':'software-smoke' if smoke else 'official-v1-r2',
        'ready':not differences and disk>=estimated_disk and ram>=estimated_ram and max(checks.values())<=1e-10,
        'dependency_differences':differences,'python':sys.executable,
        'phases':[{'name':s.name,'steps':len(s.steps)} for s in specs],
        'total_steps':sum(len(s.steps) for s in specs),'extension_n12_n16':extension and not smoke,
        'disk_estimate_bytes_uncompressed_with_margin':estimated_disk,'disk_free_bytes':disk,
        'ram_estimate_bytes_with_margin':estimated_ram,'ram_available_bytes':ram,
        'estimate_scope':'Estimativa conservadora; tempo depende da máquina e será medido. Coleta pode levar horas ou dias.',
        'independent_exact_crosscheck':checks,'ibm_jobs_submitted':0}


def _load(root, state):
    execution=audit.load_execution(root,state['execution_id'])
    protocol.verify_artifacts(root,execution)
    artifacts={Path(a['path']).name:root/a['path'] for a in execution['artifacts']}
    result=json.loads((root/execution['result']['path']).read_text())
    return execution,artifacts,result


def _arrays(artifacts, prefixes):
    with np.load(artifacts['moments.npz'],allow_pickle=False) as data:
        return {k:data[k] for k in data.files if any(k.startswith(p) for p in prefixes)}


def _cell(config):
    return json.dumps({k:config[k] for k in ('n','mu','t_max','points')},sort_keys=True)


def validate_step(root, step, result):
    """Impede ruído/mitigação com referência ideal insuficiente antes do job Aer."""
    if step.action=='circuit' and result['max_probability_difference']>1e-10:
        raise ValueError('Qiskit e emulador divergem acima de 1e-10')
    if step.action=='quantum' and 'ideal' in step.id:
        error=result['metrics']['ideal']['c3']['max_abs']
        if error>.001:
            raise ValueError(f'Grade de ruído não resolve Trotter: erro K3={error:g} > 0.001')


def analyze_phase(root, spec, record, *, smoke=False, repetitions=2000, reference_overrides=None):
    name=phase_key(spec.name)
    report={'phase':spec.name,'profile':'software-smoke' if smoke else 'official-v1-r2',
            'status':'passed','checks':[],'cases':[]}
    def check(label,value,limit):
        passed=bool(np.isfinite(value) and value<=limit)
        report['checks'].append({'name':label,'value':float(value),'limit':limit,'pass':passed})
        if not passed:
            report['status']='failed'
    groups={}
    for step,state in zip(spec.steps,record['steps'],strict=True):
        _,artifacts,result=_load(root,state)
        if step.action=='classical':
            cfg=step.request['config']; key=_cell(cfg)
            groups.setdefault(key,[]).append((step,artifacts,result))
            for c in result['quality']['controls']:
                check(f"{step.id}: {c['name']}",c['value'],c['limit'])
            if name=='01_controles':
                a=_arrays(artifacts,('exact_','mean_'))
                check(f'{step.id}: P exato/MF',np.max(np.abs(a['exact_pe']-a['mean_pe'])),1e-6)
                check(f'{step.id}: K3 sem interação',np.max(np.abs(a['exact_c3'])),1e-10)
        elif step.action=='circuit':
            check(step.id,result['max_probability_difference'],1e-10)
        elif step.action=='quantum' and name=='04_trotter':
            report['cases'].append({'id':step.id,'steps':step.request['steps'],
                                    'ideal_c3':result['metrics']['ideal']['c3']})
            if step.request['steps']==16:
                check(step.id,result['metrics']['ideal']['c3']['max_abs'],.001)
    if name=='00_reproducao_publicada':
        if smoke:
            report['scope']='Somente o caminho de execução; não valida reprodução publicada.'
        else:
            reference=np.genfromtxt(BENCHMARK/'figure2c.csv',delimiter=',',names=True,dtype=None,encoding='utf8')
            step,artifacts,_=next(iter(groups.values()))[0]
            arrays=_arrays(artifacts,('exact_m1','psa_m1'))
            times=np.linspace(0,200,step.request['config']['points'])
            for method,limit in (('exact',.02),('psa',.06)):
                for i in range(4):
                    values=reference[(reference['method']==method)&(reference['neutrino']==i)]
                    predicted=np.interp(values['t_paper'],times,arrays[f'{method}_m1'][:,i])
                    check(f'Figura 2(c): {method} ν{i}',np.max(np.abs(predicted-values['z'])),limit)
    if name=='02_integracao':
        for key,items in groups.items():
            seeds=sorted({step.request['config']['seed'] for step,_,_ in items})
            for seed in seeds:
                variants={step.request['substeps']:a for step,a,_ in items if step.request['config']['seed']==seed}
                left,right=(_arrays(variants[h],('psa_', 'mean_')) for h in (8,12))
                for prefix in ('psa','mean'):
                    for kind,limit in (('pe',1e-6),('c2',1e-5),('c3',1e-5)):
                        check(f'{key} s{seed} {prefix} {kind}',np.max(np.abs(left[f'{prefix}_{kind}']-right[f'{prefix}_{kind}'])),limit)
    if name in ('02_amostragem','02_amostragem_suplementar'):
        for key,items in groups.items():
            for m in sorted({step.request['trajectories'] for step,_,_ in items}):
                values=[_arrays(a,('psa_c3',))['psa_c3'] for step,a,_ in items if step.request['trajectories']==m]
                if name=='02_amostragem_suplementar' and len(values)!=20:
                    raise ValueError('A validação suplementar exige exatamente 20 blocos por célula')
                se=float(np.max(np.std(values,axis=0,ddof=1)/np.sqrt(len(values))))
                report['cases'].append({'cell':json.loads(key),'trajectories':m,'max_seed_standard_error_c3':se,'seeds':len(values)})
                if m==4096:
                    check(f'{key} erro padrão PSA',se,.01)
    if name in ('03_classica_principal','03_classica_extensao','05_medicoes'):
        for key,items in groups.items():
            values=[_arrays(a,('psa_m','exact_c')) for _,a,_ in items]
            blocks=[{k:v[f'psa_{k}'] for k in ('m1','m2','m3')} for v in values]
            summary=h1(blocks,values[0]['exact_c2'],values[0]['exact_c3'],json.loads(key)['n'],repetitions=repetitions)
            report['cases'].append({'cell':json.loads(key),'psa_analysis':summary})
        trends=[]
        for n in sorted({case['cell']['n'] for case in report['cases']}):
            cases=sorted((c for c in report['cases'] if c['cell']['n']==n),key=lambda c:c['cell']['mu'])
            draws=[c['psa_analysis']['r3_minus_r2_bootstrap'] for c in cases]
            trend={'n':n,'x':'log10(mu)','y':'R3-R2','scope':'Tendência exploratória por N; sementes pareadas entre mu'}
            if len(cases)>1 and all(len(d)==repetitions for d in draws):
                x=np.log10([c['cell']['mu'] for c in cases]); x-=x.mean()
                slopes=x@np.asarray(draws)/(x@x)
                central=np.array([c['psa_analysis']['c3']['normalized_rmse']-c['psa_analysis']['c2']['normalized_rmse'] for c in cases])
                trend.update(slope=float(x@central/(x@x)),ci95=list(map(float,np.quantile(slopes,[.025,.975]))))
            else:
                trend.update(slope=None,ci95=None,reason='Grade insuficiente ou normalização sem sinal resolvido')
            trends.append(trend)
        report['h1_trends']=trends
        if name=='05_medicoes':
            measurements={}
            for step,state in zip(spec.steps,record['steps'],strict=True):
                if step.action!='quantum':
                    continue
                _,a,result=_load(root,state)
                # A referência física inclui configuração e orçamento, jamais a semente.
                cell=_cell(result['config'])+'|'+str(step.request['shots'])
                measurements.setdefault(cell,[]).append(_arrays(a,('measured_m','exact_c')))
            for key,values in measurements.items():
                n=json.loads(key.split('|')[0])['n']
                blocks=[{k:v[f'measured_{k}'] for k in ('m1','m2','m3')} for v in values]
                c2,c3=pooled(blocks,n)
                report['cases'].append({'cell':json.loads(key.split('|')[0]),'shots_per_repetition':int(key.split('|')[1]),
                    'repetitions':len(blocks),'total_shots_per_time':int(key.split('|')[1])*len(blocks),
                    'measured_c2':metrics(values[0]['exact_c2'],c2),'measured_c3':metrics(values[0]['exact_c3'],c3)})
    if name in ('06_ruido','07_mitigacao'):
        report.update(analyze_endpoints(root,spec,record,repetitions=repetitions,smoke=smoke,
                                       reference_overrides=reference_overrides))
        if reference_overrides:
            report['reference_overrides']=reference_overrides
    report['hypothesis_results_are_not_acceptance_gates']=True
    return report


def analyze_endpoints(root,spec,record,*,repetitions,smoke,reference_overrides=None):
    groups={}
    states={s.id:(s,r) for s,r in zip(spec.steps,record['steps'],strict=True)}
    for step,state in zip(spec.steps,record['steps'],strict=True):
        if step.action not in ('aer','mitigation'):
            continue
        parent,ps=states[step.run_from]
        cfg=parent.request['config']
        req=step.request
        key=json.dumps({'n':cfg['n'],'mu':cfg['mu'],'tau':cfg['t_max'],'shots':req['shots'],
            'single':req['single_qubit_error'],'two':req['two_qubit_error'],'readout':req['readout_error']},sort_keys=True)
        _,a,result=_load(root,state)
        arrays=_arrays(a,('psa_m','exact_c3','ideal_c3', 'aer_', 'mitigation_'))
        t=req['interval_index']
        block={k:arrays[f'psa_{k}'][t] for k in ('m1','m2','m3')}
        override=(reference_overrides or {}).get(step.run_from)
        if override:
            reference_step,reference_state=states[override]
            if reference_step.action!='classical' or reference_step.request['config']!=cfg:
                raise ValueError('Referência PSA refinada deve manter o mesmo cenário e semente')
            _,reference_artifacts,_=_load(root,reference_state)
            reference_arrays=_arrays(reference_artifacts,('psa_m',))
            block={k:reference_arrays[f'psa_{k}'][t] for k in ('m1','m2','m3')}
        group=groups.setdefault(key,{'counts':[],'psa':[],'exact':float(arrays['exact_c3'][t,0]),'residual':0.})
        group['psa'].append(block)
        group['residual']=max(group['residual'],float(np.abs(arrays['ideal_c3'][t,0]-arrays['exact_c3'][t,0])))
        if step.action=='mitigation':
            group['counts'].append({k:arrays[v] for k,v in result['counts_keys'].items()})
        else:
            group['counts'].append(arrays[result['counts_key']])
    cases=[]
    for key,group in groups.items():
        cell=json.loads(key)
        if isinstance(group['counts'][0],dict):
            analysis=h2(group['counts'],group['psa'],group['exact'],group['residual']+1e-5,repetitions=repetitions)
        else:
            from neutrinos.mitigation import observable
            counts=np.sum(group['counts'],axis=0)
            estimate=observable(counts/counts.sum(),'c3',(0,1,2))
            analysis={'estimate':estimate,'exact':group['exact'], 'absolute_error':abs(estimate-group['exact']),
                      'scope':'Descritivo; decisão H2 bruta/mitigada pertence a T07.'}
        primary=(not smoke and cell['mu']==3. and cell['tau']==2. and cell['shots']==16384 and cell['readout']==.03)
        cases.append({'cell':cell,'primary':primary,'repetitions':len(group['counts']),
            'total_budget_per_method':cell['shots']*len(group['counts']),'analysis':analysis,
            'scope':'Teste principal predefinido' if primary else 'Sensibilidade descritiva; sem declaração confirmatória múltipla'})
    return {'endpoint_cases':cases}


def export_phase(root,spec,record,destination):
    """CSV e gráficos derivados dos momentos; nenhuma curva ilustrativa é inserida."""
    name=phase_key(spec.name)
    if name not in ('03_classica_principal','03_classica_extensao','05_medicoes'):
        return []
    os.environ.setdefault('MPLCONFIGDIR',str(root/'_cache'/'matplotlib'))
    os.environ.setdefault('XDG_CACHE_HOME',str(root/'_cache'/'fonts'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cells={}
    for step,state in zip(spec.steps,record['steps'],strict=True):
        if step.action!='classical':
            continue
        _,a,_=_load(root,state)
        cells.setdefault(_cell(step.request['config']),[]).append(_arrays(a,('psa_m','exact_c3','mean_c3')))
    artifacts=[]
    for index,(key,values) in enumerate(cells.items()):
        cell=json.loads(key); n=cell['n']; times=np.linspace(0,cell['t_max'],cell['points'])
        _,psa=pooled([{k:v[f'psa_{k}'] for k in ('m1','m2','m3')} for v in values],n)
        exact,mean=values[0]['exact_c3'],values[0]['mean_c3']
        filename=f'cell_{index:02d}_n{n}_mu{cell["mu"]}'
        path=destination/f'{filename}.csv'
        with path.open('w') as f:
            writer=csv.writer(f); writer.writerow(['tau','trio','exact_k3','psa_k3','mean_field_k3'])
            for t,tau in enumerate(times):
                for trio in range(exact.shape[1]):
                    writer.writerow([tau,trio,exact[t,trio],psa[t,trio],mean[t,trio]])
        fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
        for method,curve in (('Exact',exact),('PSA',psa),('Mean field',mean)):
            axes[0].plot(times,curve[:,0],label=method)
        axes[0].set(xlabel='τ',ylabel='Kzzz (0,1,2)',title=f'N={n}, μ={cell["mu"]}')
        axes[0].legend()
        if spec.name.startswith('smoke-'):
            fig.suptitle('SOFTWARE VALIDATION — reduced grid')
        axes[1].plot(times,np.sqrt(np.mean((psa-exact)**2,axis=1)),label='PSA RMSE across triples')
        axes[1].set(xlabel='τ',ylabel='RMSE of Kzzz',title=f'{len(values)} independent seed blocks')
        axes[1].legend()
        image=destination/f'{filename}.png'
        fig.savefig(image,dpi=180); plt.close(fig)
        artifacts.extend([path,image])
    return artifacts


def run_study(*, smoke=False, extension=True, resume: Path | None=None, progress=print,
              next_phase=False):
    import fcntl
    root=service.store.root.resolve()
    specs=smoke_specs() if smoke else official_specs(extension)
    if resume:
        path=resume.resolve()
        record=json.loads(path.read_text())
        if path.parents[2] != root or path.name!='study.json':
            raise ValueError('Retome com o mesmo --output da coleta')
        if record.get('continuation'):
            proof=record['continuation']['verification']
            proof_path=(path.parent/proof['path']).resolve()
            if (not proof_path.is_relative_to(path.parent) or
                    audit.file_hash(proof_path)!=proof['sha256']):
                label='otimização' if record['continuation']['kind']=='equivalent_solver_optimization' else 'continuação'
                raise ValueError(f'Verificação da {label} foi alterada')
        smoke=record['profile']=='software-smoke'
        extension=record['extension']
        specs=smoke_specs() if smoke else official_specs(extension)
        if record.get('protocol_specs'):
            specs=[protocol.ProtocolSpec.model_validate(s) for s in record['protocol_specs']]
            if [s.name for s in specs]!=[p['name'] for p in record['phases']]:
                raise ValueError('Plano da continuação não corresponde às fases registradas')
        if audit.environment_differences(record['environment']):
            raise ValueError('Fontes/dependências mudaram; retome com o snapshot arquivado ou inicie outra coleta')
    else:
        path=root/'studies'/audit.new_id()/'study.json'
        snapshot=audit.environment()
        record={'schema_version':1,'profile':'software-smoke' if smoke else 'official-v1-r2',
            'status':'created','started_utc':audit.utc_now(),'extension':extension,
            'environment':snapshot,'source_snapshot':audit.archive_environment(root,snapshot),
            'phases':[{'name':s.name,'status':'pending','protocol_record':None} for s in specs]}
    path.parent.mkdir(parents=True,exist_ok=True)
    with (path.parent/'.lock').open('w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Esta coleta já está ativa em outro processo') from exc
        record.update(status='running',process_id=os.getpid(),error=None,
                      last_request_mode='next_phase' if next_phase else 'remaining_phases')
        audit.atomic_json(path,record)
        audit.atomic_json(root/'studies'/'LATEST.json',{'record_path':str(path),'profile':record['profile']})
        try:
            checks=preflight(smoke=smoke,extension=extension,specs=specs)
            audit.atomic_json(path.parent/'preflight.json',checks)
            if not checks['ready']:
                raise ValueError('Preflight reprovado; consulte preflight.json')
            for spec,state in zip(specs,record['phases'],strict=True):
                if state['status']=='completed':
                    old=json.loads(Path(state['protocol_record']).read_text())
                    for step in old['steps']:
                        protocol.verify_artifacts(root,audit.load_execution(root,step['execution_id']))
                    for item in state['artifacts']:
                        if audit.file_hash(path.parent/item['path'])!=item['sha256']:
                            raise ValueError('Relatório/figura alterado após a análise')
                    continue
                analysis_only=state['status']=='analysis_pending'
                state.update(status='analyzing' if analysis_only else 'running',started_utc=audit.utc_now())
                audit.atomic_json(path,record)
                def on_record(p):
                    state['protocol_record']=str(p.resolve())
                    audit.atomic_json(path,record)
                previous=Path(state['protocol_record']) if state.get('protocol_record') else None
                progress(f'Fase: {spec.name}' + (' (reanálise dos dados salvos)' if analysis_only else ''))
                if analysis_only:
                    result=json.loads(previous.read_text())
                    if result['status']!='completed' or protocol.read_protocol(previous.parent/'protocol.json')!=spec:
                        raise ValueError('A reanálise exige protocolo concluído com os mesmos parâmetros')
                    for step in result['steps']:
                        protocol.verify_artifacts(root,audit.load_execution(root,step['execution_id']))
                else:
                    result=protocol.run_protocol(spec,resume=previous,progress=progress,on_record=on_record,
                                                 step_validator=validate_step)
                report=analyze_phase(root,spec,result,smoke=smoke,repetitions=40 if smoke else 2000,
                                     reference_overrides=state.get('reference_overrides'))
                if record.get('sampling_amendment'):
                    report['sampling_amendment']=record['sampling_amendment']
                if record.get('trotter_amendment'):
                    report['trotter_amendment']=record['trotter_amendment']
                folder=path.parent/spec.name
                folder.mkdir(exist_ok=True)
                report_path=folder/'analysis.json'
                audit.atomic_json(report_path,report)
                outputs=[report_path,*export_phase(root,spec,result,folder)]
                state['artifacts']=[{'path':str(p.relative_to(path.parent)),'sha256':audit.file_hash(p)} for p in outputs]
                state['analysis_status']=report['status']
                if report['status']!='passed':
                    state['status']='validation_failed'
                    raise ValueError(f'Controle científico reprovado em {spec.name}; consulte {report_path}')
                state.update(status='completed',finished_utc=audit.utc_now())
                audit.atomic_json(path,record)
                if next_phase:
                    break
            pending=next((p for p in record['phases'] if p['status']!='completed'),None)
            record['next_phase']=pending['name'] if pending else None
            record['status']=('awaiting_next_phase' if pending else
                              'software_validated' if smoke else 'completed_local_collection')
        except BaseException as exc:
            for phase in record['phases']:
                if phase['status']=='analyzing':
                    phase.update(status='analysis_pending',error=audit.safe_error(exc))
                elif phase['status']=='running':
                    phase.update(status='interrupted' if isinstance(exc,(KeyboardInterrupt,SystemExit)) else 'failed',
                                 error=audit.safe_error(exc))
            record['status']='interrupted' if isinstance(exc,(KeyboardInterrupt,SystemExit)) else 'failed'
            record['error']=audit.safe_error(exc)
            raise
        finally:
            record['finished_utc']=audit.utc_now()
            audit.atomic_json(path,record)
            progress(f'Registro: {path}')
    return {**record,'record_path':str(path)}


def hardware_plan(study_path, backend, *, max_depth=20000):
    """Materializa o ponto principal IBM; a execução continua explicitamente autorizada."""
    record=json.loads(study_path.read_text())
    if record['profile']!='official-v1-r2' or record['status']!='completed_local_collection':
        raise ValueError('T08 requer coleta local oficial concluída; smoke não autoriza esta fase')
    phase=next(p for p in record['phases'] if p['name']=='T07-mitigacao')
    report_path=study_path.parent/'T07-mitigacao'/'analysis.json'
    expected=next(a['sha256'] for a in phase['artifacts'] if a['path'].endswith('/analysis.json'))
    if audit.file_hash(report_path)!=expected or audit.environment_differences(record['environment']):
        raise ValueError('Fontes ou análise T07 mudaram; use a versão arquivada da coleta')
    report=json.loads(report_path.read_text())
    primary=next(c for c in report['endpoint_cases'] if c['primary'])
    if primary['analysis']['status']!='analyzed' or primary['analysis']['bounded_numerical_residual']>.001:
        raise ValueError('Calibração/precisão local insuficiente no ponto principal')
    steps=[]
    for seed in range(60001,60021):
        parent=f'ibm_s{seed}'
        steps.extend([{'id':parent,'action':'classical','request':{'config':{
            'n':4,'mu':3.,'theta':.2,'t_max':2.,'points':8,'seed':seed,'flavors':[0,0,1,1],
            'omega_values':[.7,.9,1.1,1.3]},'trajectories':4096,'substeps':12}},
            {'id':f'{parent}_ideal','action':'quantum','run_from':parent,
             'request':{'steps':16,'shots':32,'readout_error':0}}])
        for role,budget in (('raw',16384),('signal',12288),('calibration_zero',2048),('calibration_one',2048)):
            steps.append({'id':f'{parent}_{role}','action':'hardware','run_from':parent,'request':{
                'backend':backend,'interval_index':7,'steps':16,'shots':budget,'kind':'c3','index':0,
                'role':role,'calibration_reference':role.startswith('calibration'),'max_depth':max_depth}})
    spec=protocol.ProtocolSpec(name='T08-hardware',description='Ponto principal fixado; 80 jobs, 655360 shots totais (327680 por método), incluindo calibração. Enviar com --allow-hardware. Não selecionar outro caso após observar dados.',steps=steps)
    path=study_path.parent/'08_hardware.json'
    audit.atomic_json(path,spec.model_dump(mode='json'))
    audit.atomic_json(path.with_suffix('.budget.json'),{'backend':backend,'jobs':80,
        'total_shots':655360,'total_shots_per_method':327680,'max_depth':max_depth,
        'source_study':str(study_path.resolve()),'source_analysis_sha256':expected,
        'calibration_layout':'Mesmos qubits físicos finais do sinal de cada bloco; calibração completa 0000/1111',
        'scope':'Mitiga leitura independente e SPAM da calibração; não remove todo viés de portas.',
        'authorization':'Este comando não enviou jobs. run_protocol --allow-hardware autoriza os envios.'})
    return path


def collect_hardware(path):
    """Consulta jobs já enviados; nunca cria novos jobs. Contagens ficam auditadas."""
    from . import ibm_runtime
    with ibm_runtime.shared_session():
        return _collect_hardware(path)


def _collect_hardware(path):
    record=json.loads(path.read_text())
    root=service.store.root
    if path.resolve().parent.parent!=(root/'protocols').resolve():
        raise ValueError('Use o mesmo --output do protocolo IBM')
    blocks={}
    pending=[]
    for state in record['steps']:
        if state['action']!='hardware' or state['status']!='completed':
            continue
        _,_,result=_load(root,state)
        entry=result['hardware_runs'][-1]
        refreshed=service.refresh_hardware(state['run_id'],entry['job_id'])
        if refreshed['status']!='DONE':
            pending.append({'job_id':entry['job_id'],'status':refreshed['status']})
            continue
        manifest,summary,arrays=service.store.load(state['run_id'])
        cfg=manifest['config_input']; t=entry['interval_index']
        block=blocks.setdefault(state['run_id'],{'counts':{},'psa':{k:arrays[f'psa_{k}'][t] for k in ('m1','m2','m3')},
            'exact':float(arrays['exact_c3'][t,0]),'residual':float(abs(arrays['ideal_c3'][t,0]-arrays['exact_c3'][t,0]))})
        role={'raw':'raw','signal':'signal','calibration_zero':'zero','calibration_one':'one'}[entry['role']]
        block['counts'][role]=arrays[refreshed['counts_key']]
    complete=[b for b in blocks.values() if set(b['counts'])=={'raw','signal','zero','one'}]
    result={'status':'failed_jobs' if any(p['status'] in ('ERROR','CANCELLED') for p in pending) else 'awaiting_jobs','pending_jobs':pending,'complete_blocks':len(complete),
            'expected_blocks':20,'source_protocol':str(path.resolve()),'utc':audit.utc_now()}
    if record['name']=='T08-aquisicao-antecipada':
        result['scientific_status']='provisional_pending_T07_and_local_validation'
    if not pending and len(complete)==20:
        result['analysis']=h2([b['counts'] for b in complete],[b['psa'] for b in complete],
            complete[0]['exact'],max(b['residual'] for b in complete)+1e-5)
        result['status']='analyzed'
    audit.atomic_json(path.parent/'hardware_analysis.json',result)
    return result
