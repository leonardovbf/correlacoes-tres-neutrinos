"""Emenda de precisão amostral e continuação auditada de estudos interrompidos.

Nenhum resultado reprovado vira aprovação. A validação de cinco sementes fica
arquivada como condição substituída; o novo teste fixo usa vinte sementes novas.
"""
from __future__ import annotations
import copy
import fcntl
import hashlib
import json
import shutil
from pathlib import Path
from . import audit, protocol, revalidation, service, study
from .storage import ROOT

SUPPLEMENT_NAME='T02-amostragem-suplementar'
SUPPLEMENT_PATH='configs/protocols/artigo_v1/02_suplemento_amostragem_v3.json'
AMENDMENT_PATH='configs/protocols/artigo_v1/especificacoes/emenda_amostragem_v3.json'
SEEDS=tuple(range(70001,70021))


def design_files():
    original=protocol.read_protocol(ROOT/'configs/protocols/artigo_v1/02_amostragem.json')
    configs={}
    for step in original.steps:
        if step.request['trajectories']==4096:
            cfg=step.request['config']; configs[(cfg['n'],cfg['mu'])]=cfg
    steps=[]
    for (n,mu),cfg in sorted(configs.items()):
        for seed in SEEDS:
            steps.append({'id':f'n{n}_mu{str(mu).replace(".","p")}_s{seed}', 'action':'classical',
                'request':{'config':{**cfg,'seed':seed},'trajectories':4096,'substeps':12}})
    spec=protocol.ProtocolSpec(name=SUPPLEMENT_NAME,description=(
        'Emenda operacional v3, definida após falha de precisão da T02 e antes dos novos dados. '
        'Seis células N=4/8 e mu=0.1/1/10, vinte sementes independentes 70001..70020, '
        '4096 trajetórias por bloco; mesmo limite de erro-padrão máximo K3 <= 0.01. '
        'Não modifica Hamiltoniano, hipóteses, ponto principal H2, grade ou dados anteriores. '
        'Se falhar, interromper; sem aumento adaptativo silencioso.'),steps=steps)
    amendment={'schema_version':1,'id':'amostragem-precisao-v3',
        'timing':'Definida após falhas iniciais de precisão e antes da coleta suplementar; não é pré-registro original.',
        'reason':'A análise específica da T02 foi omitida por erro de encaminhamento. A revalidação identificou precisão insuficiente em três das seis células.',
        'superseded_condition':{'phase':'T02-amostragem','trajectories_per_block':4096,'seed_blocks':5,
            'preservation':'Resultados e reprovações ficam arquivados; a condição original não será rotulada como aprovada.'},
        'new_condition':{'phase':SUPPLEMENT_NAME,'protocol':SUPPLEMENT_PATH,
            'cells':[{'n':n,'mu':mu} for n,mu in sorted(configs)],
            'seed_blocks':20,'seeds':list(SEEDS),'trajectories_per_block':4096,
            'trajectories_per_cell':81920,'total_classical_executions':len(steps),'substeps':12},
        'precision_metric':'Maior erro-padrão entre sementes de Kzzz em todos os tempos e trios: std(K3_blocos, ddof=1)/sqrt(20).',
        'precision_limit':.01,
        'acceptance':'Todas as seis células devem cumprir 0.01. Nenhuma exclusão de semente/célula e nenhum aumento automático após observar o novo resultado.',
        'unchanged':['Hamiltoniano e estados iniciais','malha temporal 201 pontos em tau 0..10',
                     '4096 trajetórias por bloco','12 subpassos RK4','hipóteses H1/H2 e ponto principal H2',
                     'limites de integração, Trotter, equivalência e normalização'],
        'reuse':'Dados já coletados em T03 são preservados e reanalisados após o novo controle. Registra-se que foram coletados antes da detecção da falha.',
        'stop_policy':'Não continuar T05/T06/T07 nem IBM se a validação suplementar falhar.'}
    return {SUPPLEMENT_PATH:spec.model_dump(mode='json'),AMENDMENT_PATH:amendment}


def _verify_phase(root,phase,spec):
    source=Path(phase['protocol_record']).resolve()
    if source.parent.parent!=(root/'protocols').resolve():
        raise ValueError('Protocolo anterior fora da pasta de resultados')
    record=json.loads(source.read_text())
    if protocol.read_protocol(source.parent/'protocol.json')!=spec:
        raise ValueError('Os parâmetros físicos do protocolo anterior mudaram')
    for state in record['steps']:
        if state['status']=='completed':
            protocol.verify_artifacts(root,audit.load_execution(root,state['execution_id']))
    return source,record


def _fork_protocol(root,source,old,spec,environment,snapshot):
    """Novo diário com quatro etapas herdadas; o diário interrompido não é editado."""
    identifier=audit.new_id();folder=root/'protocols'/identifier
    normalized=spec.model_dump(mode='json')
    result=copy.deepcopy(old)
    for state in result['steps']:
        if state['status']!='completed':
            if state.get('execution_id'):
                execution=audit.load_execution(root,state['execution_id'])
                if state.get('attempts'):
                    state['attempts'][-1]['status']=execution['status']
            state.update(status='pending',error=None)
    result.update(protocol_run_id=identifier,status='prepared',process_id=None,
        environment=environment,source_snapshot=snapshot,error=None,finished_utc=None,
        protocol_sha256=hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest(),
        recovery_parent={'record':str(source),'sha256':audit.file_hash(source),
            'environment':old['environment'],
            'completed_steps_reused':[s['id'] for s in old['steps'] if s['status']=='completed']})
    audit.atomic_json(folder/'protocol.json',normalized)
    audit.atomic_json(folder/'run.json',result)
    return folder/'run.json'


def prepare(path,*,progress=print):
    root=service.store.root.resolve();path=path.resolve()
    if path.parents[2]!=root or path.name!='study.json':
        raise ValueError('Use o mesmo --output do estudo')
    with (path.parent/'.lock').open('a') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Interrompa o executor antes de preparar a recuperação') from exc
        old=json.loads(path.read_text())
        if old['profile']!='official-v1-r2':
            raise ValueError('A emenda é exclusiva do estudo oficial v1-r2')
        if old.get('sampling_amendment'):
            raise ValueError('Este estudo já contém uma emenda; retome seu próprio study.json')
        environment=audit.environment()
        revalidation.assert_analysis_revision(old['environment'],environment)
        files=design_files()
        for name,expected in files.items():
            if json.loads((ROOT/name).read_text())!=expected:
                raise ValueError('Emenda versionada não corresponde à definição: '+name)
        validation_result=revalidation.revalidate(path,progress=progress,already_locked=True)
        validation_path=Path(validation_result['record_path']);validation=json.loads(validation_path.read_text())
        failures=[p for p in validation['phases'] if p['status']=='failed']
        if validation['missing_controls'] or {p['name'] for p in failures}!={'T02-amostragem'}:
            raise ValueError('A recuperação exige somente falha amostral e todos os demais controles completos')
        specs=study.official_specs(old['extension'])
        previous={p['name']:p for p in old['phases']}
        for spec in specs:
            state=previous[spec.name]
            if state.get('protocol_record'):
                _verify_phase(root,state,spec)
        destination=root/'studies'/audit.new_id();destination.mkdir(parents=True)
        snapshot=audit.archive_environment(root,environment)
        new=copy.deepcopy(old);new.pop('continuation',None)
        new_phases=[];new_specs=[];sources=[];completed_steps_reused=0
        controls={p['name']:p for p in validation['phases']}
        for spec in specs:
            phase=copy.deepcopy(previous[spec.name])
            if spec.name=='T02-amostragem':
                new_specs.append(files[SUPPLEMENT_PATH])
                new_phases.append({'name':SUPPLEMENT_NAME,'status':'pending','protocol_record':None,
                                   'replaces_validation':{'name':phase['name'],'protocol_record':phase['protocol_record'],
                                       'result':'failed','revalidation':str(validation_path)}})
                continue
            new_specs.append(spec.model_dump(mode='json'))
            source=Path(phase['protocol_record']) if phase.get('protocol_record') else None
            original_record=json.loads(source.read_text()) if source else None
            if original_record:
                sources.append({'phase':spec.name,'path':str(source),'sha256':audit.file_hash(source)})
                completed_steps_reused+=sum(s['status']=='completed' for s in original_record['steps'])
            if spec.name in controls:
                checked=controls[spec.name]
                if checked['status']!='passed':
                    raise ValueError('Controle não aprovado')
                file=destination/spec.name/'analysis.json';file.parent.mkdir(parents=True)
                shutil.copyfile(validation_path.parent/checked['report']['path'],file)
                if audit.file_hash(file)!=checked['report']['sha256']:
                    raise ValueError('Relatório mudou durante a cópia')
                phase.update(status='completed',analysis_status='passed',analysis_revalidated_utc=audit.utc_now(),
                    artifacts=[{'path':str(file.relative_to(destination)),'sha256':audit.file_hash(file)}])
            elif original_record and original_record['status']=='completed':
                phase.update(status='analysis_pending',analysis_status='requires_reanalysis',
                    previous_analysis={'study_record':str(path),'artifacts':phase.get('artifacts',[])})
                phase.pop('artifacts',None)
            elif original_record:
                fork=_fork_protocol(root,source,original_record,spec,environment,snapshot)
                phase.update(status='pending',protocol_record=str(fork.resolve()),error=None)
                phase.pop('artifacts',None)
            new_phases.append(phase)
        proof={'schema_version':1,'kind':'sampling_precision_amendment_v3','defined_utc':audit.utc_now(),
            'parent_study':str(path),'parent_study_sha256':audit.file_hash(path),
            'parent_environment':old['environment'],'environment':environment,
            'amendment':{'path':AMENDMENT_PATH,'sha256':audit.file_hash(ROOT/AMENDMENT_PATH)},
            'supplement_protocol':{'path':SUPPLEMENT_PATH,'sha256':audit.file_hash(ROOT/SUPPLEMENT_PATH)},
            'revalidation':{'path':str(validation_path),'sha256':audit.file_hash(validation_path)},
            'superseded_sampling_validation':next(p for p in validation['phases'] if p['name']=='T02-amostragem'),
            'previous_protocols':sources,'completed_steps_reused':completed_steps_reused,
            'new_simulations_executed':0,
            'collection_deviation':'T03 e quatro etapas T05 foram coletadas antes da detecção da falha de encaminhamento. São preservadas, com reanálise após validação suplementar.'}
        proof_file=destination/'recovery.json';audit.atomic_json(proof_file,proof)
        new.update(status='awaiting_next_phase',started_utc=audit.utc_now(),finished_utc=None,process_id=None,error=None,
            environment=environment,source_snapshot=snapshot,phases=new_phases,protocol_specs=new_specs,
            next_phase=SUPPLEMENT_NAME,sampling_amendment={'id':'amostragem-precisao-v3','protocol':SUPPLEMENT_PATH},
            continuation={'kind':'sampling_precision_amendment_v3','parent_record':str(path),
                'verification':{'path':proof_file.name,'sha256':audit.file_hash(proof_file)}})
        output=destination/'study.json';audit.atomic_json(output,new)
        audit.atomic_json(root/'studies'/'LATEST.json',{'record_path':str(output),'profile':new['profile']})
        return {'record_path':str(output),'status':new['status'],'next_phase':SUPPLEMENT_NAME,
            'supplement_executions':120,'seeds_per_cell':20,'precision_limit':.01,
            'completed_steps_reused':completed_steps_reused,'new_simulations_executed':0}
