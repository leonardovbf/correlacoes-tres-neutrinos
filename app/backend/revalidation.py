"""Revalida controles após correção do encaminhamento, sem recalcular simulações."""
from __future__ import annotations
import fcntl
import json
from pathlib import Path
from . import audit, protocol, service, study

CONTROLS={'T00-reproducao-publicada','T01-controles','T02-integracao',
          'T02-amostragem','T04-trotter','T04-qiskit'}
ANALYSIS_CHANGES={'app/backend/study.py','app/backend/revalidation.py','scripts/run_study.py',
                  'app/backend/recovery.py',
                  'app/backend/hardware_queue.py',
                  'app/backend/ibm_runtime.py','app/backend/schemas.py',
                  'configs/protocols/artigo_v1/02_suplemento_amostragem_v3.json',
                  'configs/protocols/artigo_v1/especificacoes/emenda_amostragem_v3.json'}


def assert_analysis_revision(previous,current):
    if previous['dependencies']!=current['dependencies'] or previous['python']!=current['python']:
        raise ValueError('Revalide com as dependências e Python originais')
    old,new=previous['source_sha256'],current['source_sha256']
    changed=sorted(k for k in old.keys()|new.keys() if old.get(k)!=new.get(k))
    if set(changed)-ANALYSIS_CHANGES:
        raise ValueError('Mudanças fora do encaminhamento das análises: '+', '.join(set(changed)-ANALYSIS_CHANGES))
    return changed


def revalidate(path,*,progress=print,already_locked=False):
    root=service.store.root.resolve();path=path.resolve()
    if path.parents[2]!=root or path.name!='study.json':
        raise ValueError('Use o mesmo --output do estudo')
    with (path.parent/'.lock').open('a') as lock:
        if not already_locked:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError('Interrompa a coleta antes de revalidar os controles') from exc
        state=json.loads(path.read_text());environment=audit.environment()
        changed=assert_analysis_revision(state['environment'],environment)
        destination=root/'revalidations'/audit.new_id();destination.mkdir(parents=True)
        record={'schema_version':1,'status':'running','started_utc':audit.utc_now(),
            'source_study':str(path),'source_study_sha256':audit.file_hash(path),
            'original_environment':state['environment'],'environment':environment,
            'source_snapshot':audit.archive_environment(root,environment),'changed_sources':changed,
            'simulation_parameters_changed':False,'new_simulations_executed':0,'phases':[]}
        output=destination/'validation.json';audit.atomic_json(output,record)
        try:
            for phase in state['phases']:
                if phase['name'] not in CONTROLS or not phase.get('protocol_record'):
                    continue
                source=Path(phase['protocol_record']);run=json.loads(source.read_text())
                if run['status']!='completed':
                    continue
                progress('Revalidando '+phase['name'])
                spec=protocol.read_protocol(source.parent/'protocol.json')
                report=study.analyze_phase(root,spec,run,repetitions=2000)
                file=destination/(phase['name']+'.json');audit.atomic_json(file,report)
                failures=[c for c in report['checks'] if not c['pass']]
                record['phases'].append({'name':phase['name'],'status':report['status'],
                    'checks':len(report['checks']),'failed':failures,'source_protocol':str(source),
                    'source_protocol_sha256':audit.file_hash(source),
                    'report':{'path':file.name,'sha256':audit.file_hash(file)}})
                audit.atomic_json(output,record)
            missing=CONTROLS-{p['name'] for p in record['phases']}
            record['status']='failed' if any(p['status']=='failed' for p in record['phases']) else ('incomplete' if missing else 'passed')
            record['missing_controls']=sorted(missing)
            record['can_continue_official_collection']=record['status']=='passed'
            record['required_next_action']=('Controles revalidados; preparar continuação auditada.' if record['status']=='passed' else
                'Preservar os resultados. Cumprir a meta amostral com protocolo suplementar pré-definido; não reduzir a exigência para aprovar a coleta.')
        except BaseException as exc:
            record.update(status='error',error=audit.safe_error(exc));raise
        finally:
            record['finished_utc']=audit.utc_now();audit.atomic_json(output,record)
        return {'status':record['status'],'record_path':str(output),
            'can_continue_official_collection':record['can_continue_official_collection'],
            'failed_controls':[p for p in record['phases'] if p['status']=='failed'],
            'required_next_action':record['required_next_action']}
