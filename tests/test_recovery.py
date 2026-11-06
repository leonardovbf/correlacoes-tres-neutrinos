"""Retomada após emenda: preservar dados, manter limites e não repetir etapas completas."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.backend import audit,protocol,recovery,service,study
from app.backend.storage import RunStore


class RecoveryTests(unittest.TestCase):
    def test_supplement_has_fixed_new_seeds_same_physics_and_same_threshold(self):
        files=recovery.design_files()
        for name,expected in files.items():
            self.assertEqual(json.loads((recovery.ROOT/name).read_text()),expected)
        spec=protocol.ProtocolSpec.model_validate(files[recovery.SUPPLEMENT_PATH])
        cells={}
        for step in spec.steps:
            cfg=step.request['config'];cells.setdefault((cfg['n'],cfg['mu']),set()).add(cfg['seed'])
            self.assertEqual(step.request['trajectories'],4096)
            self.assertEqual(step.request['substeps'],12)
            self.assertEqual(cfg['points'],201)
            self.assertEqual(cfg['t_max'],10.)
        self.assertEqual(len(spec.steps),120)
        self.assertEqual(set(cells),{(n,mu) for n in (4,8) for mu in (.1,1.,10.)})
        for seeds in cells.values():
            self.assertEqual(seeds,set(range(70001,70021)))
            self.assertTrue(seeds.isdisjoint(range(10001,10021)))
        self.assertEqual(files[recovery.AMENDMENT_PATH]['precision_limit'],.01)
        self.assertEqual(study.phase_key(spec.name),'02_amostragem_suplementar')

    def test_forked_protocol_resumes_without_repeating_completed_work(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store;service.store=RunStore(Path(temp))
            spec=protocol.ProtocolSpec(name='recovery-fixture',steps=[{'id':f'r{i}','action':'classical',
                'request':{'config':{'n':4,'points':3,'t_max':.1,'seed':i},'trajectories':16,'substeps':1}} for i in range(2)])
            perform=protocol._perform;calls=[]
            def interrupt(step,run):
                calls.append(step.id)
                if len(calls)==2:
                    raise ValueError('interrupção de teste')
                return perform(step,run)
            try:
                with patch.object(protocol,'_perform',side_effect=interrupt):
                    with self.assertRaises(protocol.ProtocolFailed) as failed:
                        protocol.run_protocol(spec)
                source=failed.exception.record_path;before=source.read_bytes();old=json.loads(before)
                environment=audit.environment();snapshot=audit.archive_environment(Path(temp),environment)
                fork=recovery._fork_protocol(Path(temp),source,old,spec,environment,snapshot)
                with patch.object(service,'create_experiment',wraps=service.create_experiment) as create:
                    result=protocol.run_protocol(spec,resume=fork)
                    self.assertEqual(create.call_count,1)
                self.assertEqual(source.read_bytes(),before)
                self.assertEqual(result['steps'][0]['execution_id'],old['steps'][0]['execution_id'])
                self.assertNotEqual(result['protocol_run_id'],old['protocol_run_id'])
            finally:
                service.store=previous

    def test_analysis_pending_does_not_reexecute_simulations(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store;service.store=RunStore(Path(temp))
            spec=protocol.ProtocolSpec(name='T03-classica-principal',steps=[{'id':f'r{i}','action':'classical',
                'request':{'config':{'n':4,'mu':3.,'points':5,'t_max':1.,'seed':i},'trajectories':16,'substeps':4}} for i in range(2)])
            try:
                run=protocol.run_protocol(spec)
                environment=audit.environment();snapshot=audit.archive_environment(Path(temp),environment)
                path=Path(temp)/'studies'/'fixture'/'study.json'
                audit.atomic_json(path,{'profile':'official-v1-r2','extension':False,'status':'awaiting_next_phase',
                    'environment':environment,'source_snapshot':snapshot,'protocol_specs':[spec.model_dump(mode='json')],
                    'phases':[{'name':spec.name,'status':'analysis_pending','protocol_record':run['record_path']}]})
                with patch.object(study,'preflight',return_value={'ready':True}),patch.object(study,'export_phase',return_value=[]),patch.object(protocol,'run_protocol',side_effect=AssertionError('Não repetir cálculos')):
                    result=study.run_study(resume=path,next_phase=True,progress=lambda _:None)
                self.assertEqual(result['status'],'completed_local_collection')
                self.assertEqual(len(list((Path(temp)/'executions').iterdir())),2)
                analysis=json.loads((path.parent/spec.name/'analysis.json').read_text())
                self.assertEqual(len(analysis['cases']),1)
            finally:
                service.store=previous

if __name__=='__main__':
    unittest.main()
