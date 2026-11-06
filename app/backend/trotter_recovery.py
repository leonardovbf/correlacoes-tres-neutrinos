"""Emenda v4: precisão temporal na grade de ruído, com reaproveitamento auditado."""
from __future__ import annotations
import copy
import fcntl
import json
import shutil
from pathlib import Path
import numpy as np
from neutrinos.sim import ExperimentConfig,classical_exact,quantum_trotter,phase_space
from . import audit,protocol,recovery,service,study
from .storage import ROOT

DOCUMENT='configs/protocols/artigo_v1/especificacoes/emenda_discretizacao_v4.json'
LIMITS={'pe':1e-6,'c2':1e-5,'c3':1e-5}
CHANGES={'app/backend/trotter_recovery.py','app/backend/study.py','app/backend/service.py',
         'app/backend/ibm_runtime.py','src/neutrinos/qiskit_backend.py','scripts/run_study.py',DOCUMENT}


def document():
    return {'schema_version':1,'id':'discretizacao-ruido-v4',
        'reason':'Falha do circuito ideal em N4, mu10, tau4: erro K3 0.00400071 acima de 0.001. Verificação adicional encontrou precisão insuficiente na referência PSA RK12 em mu10/tau2.',
        'timing':'Definida após o controle ideal reprovar, antes de novas contagens em mu10/tau4; referências mu10/tau2 são refinadas após as contagens, que ficam preservadas.',
        'changes':[{'n':4,'mu':10.,'tau':4.,'old_points':8,'new_points':29,'substeps':12,
            'steps_per_interval':16,'total_trotter_steps':448,'phases':['T06-ruido','T07-mitigacao']},
            {'n':4,'mu':10.,'tau':2.,'points':8,'old_substeps':12,'new_substeps':24,
             'total_trotter_steps':112,'counts_policy':'Reusar contagens T06; trocar só referência PSA na análise. T07 usa RK24 desde o início.'}],
        'unchanged':['Hamiltoniano','estados e frequências','sementes','4096 trajetórias por bloco',
                     'shots e perfis de ruído','trio e tempo de observação','ponto principal H2 mu3/tau2',
                     'meta ideal K3 0.001 e metas RK Pe1e-6/C2,C3 1e-5'],
        'scope':'A profundidade do circuito mu10/tau4 aumenta. Comparações entre células devem declarar os recursos; não atribuir diferenças apenas à intensidade física da interação.',
        'preservation':'Diários e falhas originais preservados. Repetir somente referências invalidadas e etapas pendentes; nenhuma nova submissão IBM.'}


def refine_spec(spec):
    parents={s.id:s for s in spec.steps if s.action=='classical'}
    steps=[];overrides={};inserted_circuit=False
    for original in spec.steps:
        step=original.model_copy(deep=True)
        parent=original if original.action=='classical' else parents.get(original.run_from)
        cfg=parent.request['config'] if parent else {}
        target=cfg.get('n')==4 and cfg.get('mu')==10.
        if target and cfg.get('t_max')==4.:
            if original.action=='classical':
                step.request['config']['points']=29
            elif original.action in ('aer','mitigation','circuit'):
                step.request['interval_index']=28
        if target and cfg.get('t_max')==2. and original.action=='classical':
            if spec.name=='T06-ruido':
                steps.append(step)
                refined=step.model_copy(deep=True,update={'id':step.id+'_rk24_reference'})
                refined.request['substeps']=24
                steps.append(refined);overrides[step.id]=refined.id
                continue
            step.request['substeps']=24
        steps.append(step)
        if spec.name=='T06-ruido' and target and cfg.get('t_max')==4. and original.action=='quantum' and not inserted_circuit:
            steps.append(protocol.ProtocolStep(id=step.id+'_qiskit_refined',action='circuit',run_from=original.run_from,
                request={'steps':16,'interval_index':28}))
            inserted_circuit=True
    changed=spec.model_copy(update={'steps':steps,'description':spec.description+' Emenda v4 de discretização e referências, registrada no estudo.'})
    return protocol.ProtocolSpec.model_validate(changed.model_dump(mode='json')),overrides


def fork_record(root,source,old,old_spec,new_spec,environment,snapshot):
    before={s.id:s for s in old_spec.steps};states={s['id']:s for s in old['steps']}
    invalid=set();result=copy.deepcopy(old);result['steps']=[];superseded=[]
    for step in new_spec.steps:
        previous=before.get(step.id)
        unchanged=(previous is not None and previous==step and step.run_from not in invalid)
        if not unchanged:
            invalid.add(step.id)
        if step.id in states:
            state=copy.deepcopy(states[step.id])
        else:
            state={'id':step.id,'action':step.action,'status':'pending','attempts':[],
                   'execution_id':None,'run_id':None}
        if not unchanged or state['status']!='completed':
            if state.get('execution_id'):
                superseded.append({'id':step.id,'execution_id':state['execution_id'],'status':state['status'],
                                   'reason':'refinamento da grade/referência ou tentativa não concluída'})
            state.update(status='pending',run_id=None,error=None)
        result['steps'].append(state)
    path=recovery._fork_protocol(root,source,result,new_spec,environment,snapshot)
    record=json.loads(path.read_text());record['refinement_superseded_attempts']=superseded
    audit.atomic_json(path,record)
    return path,record


def reference_checks(base,destination,*,progress=print):
    report={'purpose':'convergência das referências antes da continuação','started_utc':audit.utc_now(),
            'source_environment':audit.environment(),'checks':[],'base_config':base}
    for mu,tau,points,substeps,refined in ((3.,4.,8,12,24),(10.,2.,8,24,30),(10.,4.,29,12,24)):
        for seed in list(range(30001,30021))+list(range(40001,40021)):
            cfg=ExperimentConfig.from_dict({**base,'mu':mu,'t_max':tau,'points':points,'seed':seed})
            a=phase_space(cfg,4096,substeps);b=phase_space(cfg,4096,refined)
            errors={k:float(np.max(np.abs(getattr(a,k)-getattr(b,k)))) for k in LIMITS}
            report['checks'].append({'mu':mu,'tau':tau,'points':points,'substeps':substeps,'refined':refined,
                'seed':seed,'max_differences':errors,'pass':all(errors[k]<=LIMITS[k] for k in LIMITS)})
            audit.atomic_json(destination,report)
        progress(f'Referências conferidas: mu={mu}, tau={tau}, pontos={points}')
    report['finished_utc']=audit.utc_now();audit.atomic_json(destination,report)
    return report


def prepare(path,*,checks_path=None,progress=print):
    root=service.store.root.resolve();path=path.resolve()
    if path.parents[2]!=root or path.name!='study.json':
        raise ValueError('Use o mesmo --output do estudo')
    with (path.parent/'.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('O executor ainda está ativo') from exc
        old=json.loads(path.read_text());environment=audit.environment()
        if old['status']!='failed' or not old.get('sampling_amendment'):
            raise ValueError('Esperado estudo com emenda amostral e falha de precisão na T06')
        if old['environment']['dependencies']!=environment['dependencies'] or old['environment']['python']!=environment['python']:
            raise ValueError('Não troque Python/dependências nesta recuperação')
        a,b=old['environment']['source_sha256'],environment['source_sha256']
        changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
        if changed-CHANGES:raise ValueError('Mudanças fora da recuperação: '+', '.join(sorted(changed-CHANGES)))
        if json.loads((ROOT/DOCUMENT).read_text())!=document():raise ValueError('Emenda v4 divergente')
        specs=[protocol.ProtocolSpec.model_validate(s) for s in old['protocol_specs']]
        states={p['name']:p for p in old['phases']};phase=states['T06-ruido']
        source=Path(phase['protocol_record']);previous=json.loads(source.read_text())
        failed=[s for s in previous['steps'] if s['status']=='failed']
        if len(failed)!=1 or failed[0]['action']!='quantum' or 'Grade de ruído não resolve Trotter' not in failed[0].get('error',{}).get('message',''):
            raise ValueError('A falha não corresponde ao controle de Trotter esperado')
        source_spec=protocol.read_protocol(source.parent/'protocol.json')
        base=next(s.request['config'] for s in source_spec.steps if s.id=='m4_t2_s30001')
        destination=root/'studies'/audit.new_id();destination.mkdir(parents=True)
        if checks_path:
            checks=json.loads(checks_path.read_text())
            if Path(checks.get('source_study','')).resolve()!=path or checks.get('purpose')!='diagnóstico de convergência antes de novos dados de ruído':
                raise ValueError('Diagnóstico externo não pertence ao estudo e à condição de falha')
            if checks['source_environment']['source_sha256']['src/neutrinos/sim.py']!=environment['source_sha256']['src/neutrinos/sim.py']:
                raise ValueError('Diagnóstico usa outro solver')
            if checks['source_environment']['dependencies']!=environment['dependencies']:
                raise ValueError('Diagnóstico usa outras dependências')
            shutil.copyfile(checks_path,destination/'reference_checks.json')
        else:checks=reference_checks(base,destination/'reference_checks.json',progress=progress)
        expected={(mu,tau,points,h,refined,seed) for mu,tau,points,h,refined in ((3.,4.,8,12,24),(10.,2.,8,24,30),(10.,4.,29,12,24))
                  for seed in list(range(30001,30021))+list(range(40001,40021))}
        actual={(c['mu'],c['tau'],c['points'],c['substeps'],c['refined'],c['seed']) for c in checks['checks']}
        if actual!=expected or len(checks['checks'])!=120 or any(not all(c['max_differences'][k]<=LIMITS[k] for k in LIMITS) for c in checks['checks']):
            raise ValueError('Referências refinadas não passaram em todos os 120 controles')
        cfg=ExperimentConfig.from_dict({**base,'points':29});exact=classical_exact(cfg);ideal,_=quantum_trotter(cfg,16,32,0.)
        error=float(np.max(np.abs(exact.c3-ideal.c3)))
        if error>.001:raise ValueError('A grade refinada não passou na precisão ideal')
        snapshot=audit.archive_environment(root,environment);new=copy.deepcopy(old);new_specs=[];new_states=[];overrides={};reuse=0
        for spec in specs:
            state=copy.deepcopy(states[spec.name]);progress('Verificando artefatos: '+spec.name)
            if state.get('protocol_record'):
                recovery._verify_phase(root,state,spec)
            if spec.name in ('T06-ruido','T07-mitigacao'):
                refined,refmap=refine_spec(spec);new_specs.append(refined.model_dump(mode='json'))
                state.update(status='pending',error=None,reference_overrides=refmap)
                if spec.name=='T06-ruido':
                    fork,record=fork_record(root,source,previous,spec,refined,environment,snapshot)
                    state['protocol_record']=str(fork.resolve());reuse=sum(s['status']=='completed' for s in record['steps'])
                    overrides=refmap
                state.pop('artifacts',None)
            else:
                if state['status']!='completed':raise ValueError('Uma fase anterior não foi concluída')
                new_specs.append(spec.model_dump(mode='json'))
                for artifact in state['artifacts']:
                    target=destination/artifact['path'];target.parent.mkdir(parents=True,exist_ok=True)
                    source_file=path.parent/artifact['path']
                    if audit.file_hash(source_file)!=artifact['sha256']:raise ValueError('Artefato anterior alterado')
                    shutil.copyfile(source_file,target)
            new_states.append(state)
        proof={'kind':'discretizacao-ruido-v4','defined_utc':audit.utc_now(),'parent_study':str(path),
            'parent_study_sha256':audit.file_hash(path),'parent_environment':old['environment'],
            'changed_sources':sorted(changed),'amendment':{'path':DOCUMENT,'sha256':audit.file_hash(ROOT/DOCUMENT)},
            'reference_checks':{'path':'reference_checks.json','sha256':audit.file_hash(destination/'reference_checks.json')},
            'refined_points':29,'total_trotter_steps':448,'ideal_max_c3_error':error,'limit':.001,
            'reference_overrides':overrides,'T06_completed_steps_reused':reuse,'new_simulations_executed':0}
        proof_file=destination/'trotter_recovery.json';audit.atomic_json(proof_file,proof)
        if audit.environment()['fingerprint']!=environment['fingerprint']:raise ValueError('Fontes mudaram durante a preparação')
        new.update(status='awaiting_next_phase',started_utc=audit.utc_now(),finished_utc=None,error=None,process_id=None,
            environment=environment,source_snapshot=snapshot,phases=new_states,protocol_specs=new_specs,next_phase='T06-ruido',
            trotter_amendment={'id':'discretizacao-ruido-v4','document':DOCUMENT},
            continuation={'kind':'discretizacao-ruido-v4','parent_record':str(path),
                'verification':{'path':proof_file.name,'sha256':audit.file_hash(proof_file)}})
        output=destination/'study.json';audit.atomic_json(output,new)
        audit.atomic_json(root/'studies'/'LATEST.json',{'record_path':str(output),'profile':new['profile']})
        return {'record_path':str(output),'next_phase':'T06-ruido','completed_T06_steps_reused':reuse,
                'ideal_max_c3_error':error,'refined_points':29,'total_trotter_steps':448,
                'pending_T06_steps':len(next(s for s in new_specs if s['name']=='T06-ruido')['steps'])-reuse}
