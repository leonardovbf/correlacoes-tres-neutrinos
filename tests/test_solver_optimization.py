"""Otimização deve preservar EDO, amostras e a proveniência das fases herdadas."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from app.backend import audit, optimization, protocol, service, study
from app.backend.storage import RunStore
from neutrinos.sim import ExperimentConfig, _evolve_spins, _rhs


def reference_evolution(config, spins, substeps):
    values=[spins.copy()]
    dt=float(config.times[1])/substeps
    for _ in config.times[1:]:
        for _ in range(substeps):
            a=_rhs(config,spins)
            b=_rhs(config,spins+dt*a/2)
            c=_rhs(config,spins+dt*b/2)
            d=_rhs(config,spins+dt*c)
            spins=spins+dt*(a+2*b+2*c+d)/6
        values.append(spins.copy())
    return np.stack(values)


class SolverOptimizationTests(unittest.TestCase):
    def test_uniform_arbitrary_and_nearly_uniform_couplings_match_original_rhs(self):
        rng=np.random.default_rng(30)
        spins=rng.normal(size=(32,4,3))
        near=np.ones((4,4))-np.eye(4); near[0,1]+=1e-7; near[1,0]+=1e-7
        general=np.array([[0,1,.3,-.2],[1,0,.5,.7],[.3,.5,0,1.2],[-.2,.7,1.2,0]])
        for matrix in (None,np.ones((4,4))-np.eye(4),near,general):
            for substeps in (1,4,12):
                with self.subTest(matrix=matrix,substeps=substeps):
                    cfg=ExperimentConfig(t_max=.5,points=8,mu=3.,b_values=(.6,.8,0),
                        g_values=None if matrix is None else tuple(map(tuple,matrix)))
                    expected=reference_evolution(cfg,spins.copy(),substeps)
                    actual=_evolve_spins(cfg,spins.copy(),substeps)
                    np.testing.assert_allclose(actual,expected,atol=1e-12,rtol=1e-12)

    def test_upgrade_rejects_physical_protocol_or_dependency_changes(self):
        previous={'dependencies':{'numpy':'1'},'python':'3','source_sha256':{
            'src/neutrinos/sim.py':'old','configs/protocols/artigo_v1/03_classica_principal.json':'original'}}
        current=json.loads(json.dumps(previous))
        current['source_sha256']['src/neutrinos/sim.py']='new'
        self.assertEqual(optimization._changes(previous,current),['src/neutrinos/sim.py'])
        current['source_sha256']['configs/protocols/artigo_v1/03_classica_principal.json']='changed'
        with self.assertRaisesRegex(ValueError,'fora da otimização'):
            optimization._changes(previous,current)
        current=json.loads(json.dumps(previous));current['dependencies']['numpy']='2'
        with self.assertRaisesRegex(ValueError,'dependências'):
            optimization._changes(previous,current)

    def test_continuation_preserves_original_and_completed_executions(self):
        with tempfile.TemporaryDirectory() as temp:
            original_store=service.store; service.store=RunStore(Path(temp))
            specs=[protocol.ProtocolSpec(name=f'smoke-phase{i}',steps=[{
                'id':'r','action':'classical','request':{'config':{'points':3,'t_max':.1},'trajectories':16,'substeps':1}}]) for i in range(2)]
            try:
                with patch.object(study,'smoke_specs',return_value=specs),patch.object(study,'preflight',return_value={'ready':True}),patch.object(study,'analyze_phase',return_value={'status':'passed'}):
                    result=study.run_study(smoke=True,next_phase=True,progress=lambda _:None)
                    original=Path(result['record_path']); before=original.read_bytes()
                    def verified(root,record,path,**kwargs):
                        report={'status':'passed','current_fingerprint':audit.environment()['fingerprint'],'benchmark':{'speedup':3.}}
                        audit.atomic_json(path,report)
                        return report
                    with patch.object(optimization,'verify',side_effect=verified):
                        continuation=optimization.prepare_continuation(original,progress=lambda _:None)
                    new_path=Path(continuation['record_path'])
                    self.assertNotEqual(new_path,original)
                    self.assertEqual(original.read_bytes(),before)
                    new=json.loads(new_path.read_text())
                    self.assertEqual(new['phases'][0]['protocol_record'],result['phases'][0]['protocol_record'])
                    self.assertEqual(new['continuation']['parent_record_sha256'],audit.file_hash(original))
                    completed=study.run_study(resume=new_path,next_phase=True,progress=lambda _:None)
                    self.assertEqual(completed['status'],'software_validated')
                    proof=new_path.parent/new['continuation']['verification']['path']
                    proof.write_text('{}')
                    with self.assertRaisesRegex(ValueError,'otimização foi alterada'):
                        study.run_study(resume=new_path,progress=lambda _:None)
            finally:
                service.store=original_store

    def test_active_or_failed_study_cannot_be_adopted(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            try:
                path=Path(temp)/'studies'/'example'/'study.json';path.parent.mkdir(parents=True)
                for status in ('running','failed'):
                    audit.atomic_json(path,{'status':status})
                    with self.assertRaisesRegex(ValueError,'entre fases'):
                        optimization.prepare_continuation(path,progress=lambda _:None)
            finally:
                service.store=previous

if __name__=='__main__':
    unittest.main()
