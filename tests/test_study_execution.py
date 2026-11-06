"""Verifica matemática, gates e retomada sem lançar a coleta oficial nem jobs IBM."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from app.backend import cache, protocol, service, study
from app.backend.schemas import ClassicalRequest
from app.backend.storage import RunStore
from neutrinos.sim import ExperimentConfig, phase_space, initial_state, _symmetric_trotter_step
from neutrinos.mitigation import correct, observable, response_matrix
from neutrinos.study_analysis import h2, independent_exact_check


class StudyExecutionTests(unittest.TestCase):
    def test_psa_batches_preserve_draws_and_all_moments(self):
        config=ExperimentConfig(points=5,t_max=.3,seed=12)
        left=phase_space(config,80,2,batch_size=80)
        right=phase_space(config,80,2,batch_size=13)
        for key in ('sample_z','bloch','m1','m2','m3'):
            np.testing.assert_allclose(getattr(left,key),getattr(right,key),atol=1e-14)
        large=phase_space(ExperimentConfig(points=2,t_max=.01),10000,1)
        self.assertEqual(large.sample_z.shape,(2,10000,4))

    def test_readout_inverse_respects_bit_order_and_negative_quasiprobabilities(self):
        p0=.1; p1=.2
        single=np.array([[1-p0,p1],[p0,1-p1]])
        response=np.kron(single,np.kron(single,single))
        zero=np.rint(response[:,0]*100000).astype(int)
        one=np.rint(response[:,-1]*100000).astype(int)
        actual=np.array([.5,-.01,.02,.03,.04,.05,.06,.31])
        measured=response@actual
        signal=np.rint(measured*10000000).astype(int)
        corrected,condition=correct(signal,zero,one)
        np.testing.assert_allclose(corrected,actual,atol=1e-6)
        self.assertLess(corrected[1],0)
        self.assertLess(condition,10)
        # Qubit 0 é o bit menos significativo.
        self.assertAlmostEqual(observable(np.eye(8)[1],'pe',(0,)),0)
        self.assertAlmostEqual(observable(np.eye(8)[1],'pe',(2,)),1)

    def test_singular_calibration_is_recorded_unresolved(self):
        calibration=np.ones(16,dtype=int)*100
        q,condition=correct(calibration,calibration,calibration)
        self.assertIsNone(q)
        self.assertGreater(condition,10)

    def test_h2_joint_bootstrap_distinguishes_gate_bias_from_mitigated_signal(self):
        n=4; b=2000000
        single=np.array([[.9,.1],[.1,.9]])
        response=np.array([[1.]])
        for _ in range(n):
            response=np.kron(response,single)
        p=np.zeros(16); p[0]=.7; p[-1]=.3
        counts=lambda probs,size: np.rint(probs*size).astype(int)
        block={'raw':counts(response@p,b),'signal':counts(response@p,3*b//4),
               'zero':counts(response[:,0],b//8),'one':counts(response[:,-1],b//8)}
        psa={'m1':np.zeros(4),'m2':np.zeros(6),'m3':np.zeros(4)}
        result=h2([block]*20,[psa]*20,observable(p,'c3',(0,1,2)),1e-5,repetitions=80)
        self.assertEqual(result['h2_decision'],'apoio_nesta_condicao')
        self.assertFalse(result['methods']['raw']['resolves'])
        self.assertTrue(result['methods']['mitigated']['resolves'])

    def test_qiskit_late_time_matches_emulator(self):
        from neutrinos.qiskit_backend import first_interval_probabilities
        config=ExperimentConfig(points=8,t_max=2.,mu=3)
        _,p=first_interval_probabilities(config,2,7)
        state=initial_state(config)
        for _ in range(14):
            _symmetric_trotter_step(state,config,float(config.times[1])/2)
        np.testing.assert_allclose(p,np.abs(state)**2,atol=1e-12)

    def test_independent_dense_hamiltonian_crosscheck(self):
        self.assertLess(max(independent_exact_check().values()),1e-10)

    def test_cache_reuses_only_seed_independent_physics_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); calls=[]
            def compute():
                calls.append(1)
                return {'p':np.arange(3.)}
            _,hit=cache.arrays(root,'test',ExperimentConfig(seed=1),{'steps':2},compute)
            self.assertFalse(hit)
            _,hit=cache.arrays(root,'test',ExperimentConfig(seed=7),{'steps':2},compute)
            self.assertTrue(hit)
            cache.arrays(root,'test',ExperimentConfig(seed=7,mu=3),{'steps':2},compute)
            self.assertEqual(len(calls),2)
            file=next(root.rglob('arrays.npz')); file.write_bytes(b'corrupted')
            config=ExperimentConfig(seed=1)
            # Corrompe todos os arquivos para não depender da ordem do diretório.
            for file in root.rglob('arrays.npz'):
                file.write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError,'Cache alterado'):
                cache.arrays(root,'test',config,{'steps':2},compute)

    def test_bad_discretization_stops_before_noise(self):
        step=protocol.ProtocolStep(id='r_ideal',action='quantum',run_id='existing')
        with self.assertRaisesRegex(ValueError,'Trotter'):
            study.validate_step(Path('/tmp'),step,{'metrics':{'ideal':{'c3':{'max_abs':.02}}}})

    def test_study_resume_skips_completed_phase_and_verifies_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            ref={'id':'r','action':'classical','request':{'config':{'points':3,'t_max':.1},'trajectories':16,'substeps':1}}
            specs=[protocol.ProtocolSpec(name=f'smoke-phase{i}',steps=[ref]) for i in range(2)]
            original=study.analyze_phase
            attempts=[]
            def analysis(*args,**kwargs):
                attempts.append(args[1].name)
                if len(attempts)==2:
                    raise ValueError('interrupted analysis')
                return {'status':'passed'}
            try:
                with patch.object(study,'smoke_specs',return_value=specs),patch.object(study,'preflight',return_value={'ready':True}),patch.object(study,'analyze_phase',side_effect=analysis):
                    with self.assertRaisesRegex(ValueError,'interrupted'):
                        study.run_study(smoke=True,progress=lambda _:None)
                    path=next((Path(temp)/'studies').glob('*/study.json'))
                    state=json.loads(path.read_text())
                    ids=[json.loads(Path(p['protocol_record']).read_text())['steps'][0]['execution_id'] for p in state['phases']]
                    result=study.run_study(resume=path,progress=lambda _:None)
                    after=[json.loads(Path(p['protocol_record']).read_text())['steps'][0]['execution_id'] for p in result['phases']]
                    self.assertEqual(ids,after)
                    self.assertEqual(attempts.count('smoke-phase0'),1)
                    artifact=path.parent/result['phases'][0]['artifacts'][0]['path']
                    artifact.write_text('{}')
                    with self.assertRaisesRegex(ValueError,'alterado'):
                        study.run_study(resume=path,progress=lambda _:None)
            finally:
                service.store=previous

    def test_next_phase_advances_one_phase_and_preserves_completed_results(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            ref={'id':'r','action':'classical','request':{'config':{'points':3,'t_max':.1},'trajectories':16,'substeps':1}}
            specs=[protocol.ProtocolSpec(name=f'smoke-phase{i}',steps=[ref]) for i in range(3)]
            try:
                with patch.object(study,'smoke_specs',return_value=specs),patch.object(study,'preflight',return_value={'ready':True}),patch.object(study,'analyze_phase',return_value={'status':'passed'}) as analyze:
                    first=study.run_study(smoke=True,next_phase=True,progress=lambda _:None)
                    path=Path(first['record_path'])
                    self.assertEqual(first['status'],'awaiting_next_phase')
                    self.assertEqual(first['next_phase'],'smoke-phase1')
                    self.assertEqual([p['status'] for p in first['phases']],['completed','pending','pending'])
                    self.assertIsNone(first['phases'][1]['protocol_record'])
                    original=Path(first['phases'][0]['protocol_record']).read_bytes()
                    second=study.run_study(resume=path,next_phase=True,progress=lambda _:None)
                    self.assertEqual(second['status'],'awaiting_next_phase')
                    self.assertEqual(second['next_phase'],'smoke-phase2')
                    self.assertEqual(Path(second['phases'][0]['protocol_record']).read_bytes(),original)
                    third=study.run_study(resume=path,next_phase=True,progress=lambda _:None)
                    self.assertEqual(third['status'],'software_validated')
                    self.assertIsNone(third['next_phase'])
                    self.assertEqual(analyze.call_count,3)
                    study.run_study(resume=path,next_phase=True,progress=lambda _:None)
                    self.assertEqual(analyze.call_count,3)
            finally:
                service.store=previous

    def test_next_phase_still_stops_on_failed_scientific_control(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            ref={'id':'r','action':'classical','request':{'config':{'points':3,'t_max':.1},'trajectories':16,'substeps':1}}
            specs=[protocol.ProtocolSpec(name=f'smoke-phase{i}',steps=[ref]) for i in range(2)]
            try:
                with patch.object(study,'smoke_specs',return_value=specs),patch.object(study,'preflight',return_value={'ready':True}),patch.object(study,'analyze_phase',return_value={'status':'failed'}):
                    with self.assertRaisesRegex(ValueError,'Controle científico reprovado'):
                        study.run_study(smoke=True,next_phase=True,progress=lambda _:None)
                    path=next((Path(temp)/'studies').glob('*/study.json'))
                    state=json.loads(path.read_text())
                    self.assertEqual(state['status'],'failed')
                    self.assertEqual(state['phases'][0]['status'],'validation_failed')
                    self.assertEqual(state['phases'][1]['status'],'pending')
                    self.assertIsNone(state['phases'][1]['protocol_record'])
            finally:
                service.store=previous

    def test_ibm_depth_guard_prevents_submission(self):
        from unittest.mock import Mock
        from qiskit_ibm_runtime.fake_provider import FakeBelemV2
        from app.backend import ibm_runtime
        from app.backend.schemas import HardwareRequest
        cloud=Mock(); cloud.backend.return_value=FakeBelemV2()
        sampler=Mock()
        with patch.object(ibm_runtime,'_service',return_value=cloud),patch('qiskit_ibm_runtime.executor_sampler.Sampler',return_value=sampler):
            with self.assertRaisesRegex(ValueError,'Profundidade'):
                ibm_runtime.submit(ExperimentConfig(n=2,flavors=(0,1),points=3,t_max=.1),
                    HardwareRequest(backend='offline',steps=1,max_depth=1))
        sampler.run.assert_not_called()

    def test_ibm_calibration_uses_signal_physical_qubits(self):
        from unittest.mock import Mock
        from app.backend.schemas import HardwareRequest, QuantumRequest
        from app.backend import ibm_runtime
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            try:
                run=service.create_experiment(ClassicalRequest(config={'n':2,'flavors':[0,1],'points':3,'t_max':.1},trajectories=16,substeps=1))['run_id']
                service.run_quantum(run,QuantumRequest(steps=1,shots=32))
                returned={'backend':'offline','job_id':'signal','transpilation':{'physical_qubits':[3,1]}}
                with patch.object(ibm_runtime,'submit',return_value=returned):
                    service.submit_hardware(run,HardwareRequest(backend='offline',steps=1,shots=32))
                with patch.object(ibm_runtime,'submit',return_value={**returned,'job_id':'calibration'}) as submit:
                    service.submit_hardware(run,HardwareRequest(backend='offline',steps=1,shots=32,role='calibration_zero',calibration_reference=True))
                    request=submit.call_args.args[1]
                    self.assertEqual(request.initial_layout,[3,1])
                    self.assertEqual(request.role,'calibration_zero')
            finally:
                service.store=previous

    def test_mitigation_replay_compares_counts_across_different_revision_keys(self):
        from app.backend import audit
        from app.backend.schemas import MitigationRequest, QuantumRequest
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store; service.store=RunStore(Path(temp))
            try:
                run=service.create_experiment(ClassicalRequest(config={'points':3,'t_max':.1},trajectories=16,substeps=1))['run_id']
                service.run_quantum(run,QuantumRequest(steps=1,shots=32,readout_error=0))
                def worker(*args,**kwargs):
                    raw=[256]+[0]*15; signal=[192]+[0]*15
                    zero=[32]+[0]*15; one=[0]*15+[32]
                    return {'counts':dict(raw=raw,signal=signal,zero=zero,one=one),'metadata':{}}
                request=MitigationRequest(interval_index=1,steps=1,shots=256)
                with patch.object(service,'_qiskit_worker',side_effect=worker):
                    service.run_mitigation(run,request)
                    second=service.run_mitigation(run,request)
                    self.assertIn('0002',second['counts_keys']['raw'])
                    execution=service.store.root/'executions'/audit.last_execution_id()/'execution.json'
                    result=protocol.replay_execution(execution)
                self.assertTrue(result['comparison']['pass'])
            finally:
                service.store=previous

    def test_smoke_cannot_prepare_official_hardware(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'study.json'
            path.write_text(json.dumps({'profile':'software-smoke','status':'software_validated'}))
            with self.assertRaisesRegex(ValueError,'oficial'):
                study.hardware_plan(path,'ibm_test')

if __name__=='__main__':
    unittest.main()
