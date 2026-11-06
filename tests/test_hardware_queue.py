"""Fila antecipada preparada offline; teste nenhum envia jobs reais."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from app.backend import audit,hardware_queue,ibm_runtime,protocol,service,study
from app.backend.storage import RunStore


class HardwareQueueTests(unittest.TestCase):
    def test_enqueue_requires_explicit_hardware_flag(self):
        with self.assertRaisesRegex(ValueError,'allow-hardware'):
            hardware_queue.enqueue(Path('/missing'))

    def test_preparation_keeps_budget_calibration_and_provisional_status(self):
        from qiskit_ibm_runtime.fake_provider import FakeBelemV2
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store;service.store=RunStore(Path(temp))
            path=Path(temp)/'studies'/'example'/'study.json'
            audit.atomic_json(path,{'profile':'official-v1-r2','status':'failed'})
            cloud=Mock();cloud.backend.return_value=FakeBelemV2()
            try:
                with patch.object(ibm_runtime,'list_backends',return_value=[{'name':'fake_belem','num_qubits':5}]),patch.object(ibm_runtime,'_service',return_value=cloud):
                    prepared=hardware_queue.prepare(path,'fake_belem',max_depth=100000,progress=lambda _:None)
                record=Path(prepared['queue_record']);data=json.loads(record.read_text())
                self.assertEqual(data['status'],'prepared')
                self.assertEqual(data['scientific_status'],'provisional_pending_local_precision_and_T07')
                spec=protocol.read_protocol(record.parent/'protocol.json')
                hardware=[s for s in spec.steps if s.action=='hardware']
                self.assertEqual(len(hardware),80)
                self.assertEqual(sum(s.request['shots'] for s in hardware),655360)
                self.assertEqual(sum(s.request['shots'] for s in hardware if s.request['role']=='raw'),327680)
                self.assertTrue(all(s.request['calibration_reference'] for s in hardware if s.request['role'].startswith('calibration')))
                signals=[s for s in hardware if s.request['role'] in ('raw','signal')]
                self.assertEqual({s.request['transpiler_seed'] for s in hardware},{60001})
                self.assertEqual(len({tuple(s.request['initial_layout']) for s in signals}),1)
                self.assertLessEqual(data['ideal_max_c3_error'],.001)
                fake={'steps':[{'action':'hardware','status':'completed'}]*80}
                def run(spec,**kwargs):
                    self.assertTrue(kwargs['allow_hardware'])
                    self.assertIs(kwargs['step_validator'],study.validate_step)
                    kwargs['on_record'](Path(temp)/'protocols'/'fake'/'run.json')
                    return fake
                with patch.object(protocol,'run_protocol',side_effect=run):
                    result=hardware_queue.enqueue(record,allow_hardware=True,progress=lambda _:None)
                self.assertEqual(result['submitted_jobs'],80)
                self.assertEqual(result['status'],'submitted')
            finally:
                service.store=previous

if __name__=='__main__':
    unittest.main()
