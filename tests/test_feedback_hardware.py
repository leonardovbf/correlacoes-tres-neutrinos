import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock,patch

from qiskit import QuantumCircuit

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
import run_feedback_hardware as runner


def state():
    return {'windows':[],'jobs':[{'block':i,'calibration_window':i//4,'job_id':None,'status':'planned',
        'slot':f'b{i}','pub_order':[6,8] if i%2==0 else [8,6]} for i in range(20)]}


class FeedbackHardwareTests(unittest.TestCase):
    def test_current_sdk_keeps_two_pubs_and_actual_shot_budget(self):
        plan=runner.read(runner.SOURCE/'hardware_confirmation_plan.json')
        circuits=runner.validate_plan(plan,runner.SOURCE)
        for order in [[6,8],[8,6]]:
            program,options=runner.prepare_program(circuits,order,0)
            self.assertEqual(program.shots,128);self.assertEqual([tuple(x.shape) for x in program.items],[(32,),(32,)])
            self.assertEqual([x.circuit.num_clbits for x in program.items],order)
            self.assertEqual(sum(32*program.shots for _ in program.items),8192)

    def test_plan_cannot_expand_job_or_shot_caps(self):
        plan=runner.read(runner.SOURCE/'hardware_confirmation_plan.json')
        for key,value in [('maximum_jobs',21),('total_shots',200000),('shots_per_pub',8192)]:
            modified=copy.deepcopy(plan);modified['policy'][key]=value
            with self.assertRaises(ValueError):runner.validate_plan(modified,runner.SOURCE)

    def test_window_does_not_advance_while_jobs_pending(self):
        s=state()
        for i in range(4):s['jobs'][i].update(job_id=f'j{i}',status='QUEUED')
        self.assertEqual(runner.eligible_window(s,'new'),(None,'awaiting_current_window_results'))

    def test_next_window_requires_changed_relevant_calibration(self):
        s=state();s['windows']=[{'window':0,'fingerprint':'old'}]
        for i in range(4):s['jobs'][i].update(job_id=f'j{i}',status='DONE')
        self.assertEqual(runner.eligible_window(s,'old'),(None,'awaiting_new_calibration'))
        self.assertEqual(runner.eligible_window(s,'new'),(1,'new_calibration_window'))

    def test_uncertain_submission_blocks_all_new_jobs(self):
        s=state();s['jobs'][0]['status']='submission_uncertain'
        self.assertEqual(runner.eligible_window(s,'new'),(None,'submission_uncertain'))

    def test_failed_job_is_not_replaced(self):
        s=state();s['jobs'][0].update(job_id='j0',status='ERROR')
        self.assertEqual(runner.eligible_window(s,'new'),(None,'hardware_job_failed_no_auto_replacement'))

    def test_calibration_fingerprint_ignores_unused_qubits(self):
        circuit=QuantumCircuit(2);circuit.sx(0)
        props={'qubits':[[{'name':'T1','value':1}],[{'name':'T1','value':2}]],'gates':[]}
        a=runner.fingerprint(props,{6:circuit});props['qubits'][1][0]['value']=9
        self.assertEqual(a,runner.fingerprint(props,{6:circuit}))
        props['qubits'][0][0]['value']=3
        self.assertNotEqual(a,runner.fingerprint(props,{6:circuit}))

    def test_calibration_fingerprint_ignores_status_heartbeats_and_list_order(self):
        circuit=QuantumCircuit(1);circuit.sx(0)
        props={'qubits':[[{'name':'T1','value':1},{'name':'T2','value':2},{'name':'operational','value':1,'date':'old'}]],
            'gates':[{'gate':'sx','qubits':[0],'parameters':[{'name':'gate_error','value':.001},{'name':'operational','value':1,'date':'old'}]}]}
        expected=runner.fingerprint(props,{6:circuit})
        props['qubits'][0][-1]['date']='new';props['gates'][0]['parameters'][-1]['date']='new'
        props['qubits'][0].reverse();props['gates'][0]['parameters'].reverse()
        self.assertEqual(expected,runner.fingerprint(props,{6:circuit}))

    def test_post_failure_is_persisted_and_never_automatically_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);s=state();slot=s['jobs'][0]
            converter=MagicMock();converter.model_dump_json.return_value='{}'
            with patch.object(runner,'prepare_program',return_value=(MagicMock(),MagicMock())),patch(
                'qiskit_ibm_runtime.quantum_program.converters.converters_1_1.quantum_program_to_1_1',return_value=converter),patch(
                'qiskit_ibm_runtime.executor.Executor') as executor:
                executor.return_value.run.side_effect=RuntimeError('Ambiguous server response')
                with self.assertRaises(RuntimeError):runner.submit_one(output,MagicMock(),{},s,slot)
                self.assertEqual(runner.read(output/'state.json')['jobs'][0]['status'],'submission_uncertain')
                with self.assertRaises(ValueError):runner.submit_one(output,MagicMock(),{},s,slot)
                self.assertEqual(executor.return_value.run.call_count,1)

    def finished_campaign(self,output):
        import numpy as np
        rng=np.random.default_rng(1);s=state();plan={'cases':[{'n':n,'trio':[0,1,2],'exact':.3,'psa_full_support':.1} for n in (6,8)]}
        runner.save(output/'execution_plan.json',plan);s['execution_plan_sha256']=runner.sha(output/'execution_plan.json')
        s.update(submitted_jobs=20,reserved_shots=163840,windows=[])
        for w in range(5):
            runner.save(output/f'w{w}.json',{'w':w});s['windows'].append({'window':w,'fingerprint':f'f{w}','path':f'w{w}.json','sha256':runner.sha(output/f'w{w}.json')})
        for i,j in enumerate(s['jobs']):
            counts={str(n):rng.multinomial(4096,np.ones(1<<n)/(1<<n)).tolist() for n in (6,8)}
            runner.save(output/f'c{i}.json',{'counts':counts})
            j.update(job_id=f'id{i}',status='DONE',counts_path=f'c{i}.json',counts_sha256=runner.sha(output/f'c{i}.json'))
        runner.save(output/'state.json',s);runner.save(output/'analysis.json',runner.compute_analysis(output,s,plan))

    def test_verify_accepts_complete_campaign_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);self.finished_campaign(output)
            runner.verify(output)
            analysis=runner.read(output/'analysis.json');analysis['cases'][0]['estimate']+=.01;runner.save(output/'analysis.json',analysis)
            with self.assertRaises(ValueError):runner.verify(output)
            self.finished_campaign(output);runner.save(output/'c3.json',{'counts':{'6':[0]*64,'8':[0]*256}})
            with self.assertRaises(ValueError):runner.verify(output)

    def test_verify_rejects_repeated_calibration_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);self.finished_campaign(output)
            s=runner.read(output/'state.json');s['windows'][4]['fingerprint']='f0';runner.save(output/'state.json',s)
            with self.assertRaises(ValueError):runner.verify(output)

    def test_stop_marker_prevents_network_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'STOP').write_text('stop')
            with patch.object(runner,'initialize',return_value=({}, {}, state())):
                self.assertEqual(runner.tick(output,MagicMock(),allow_hardware=True),'stopped_by_user')

if __name__=='__main__':unittest.main()
