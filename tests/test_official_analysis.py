"""Nomes oficiais devem acionar análises científicas, inclusive gates que reprovam."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from app.backend import protocol,service,study
from app.backend.storage import RunStore


class OfficialAnalysisTests(unittest.TestCase):
    def test_all_official_phase_names_route_to_their_file_stems(self):
        for stem,spec in zip(study.ORDER,study.official_specs(),strict=True):
            self.assertEqual(study.phase_key(spec.name),stem)
            self.assertEqual(study.phase_key('smoke-'+stem),stem)

    def test_official_sampling_name_triggers_failed_precision_gate(self):
        config={'n':4,'mu':10.,'t_max':10.,'points':201}
        spec=protocol.ProtocolSpec(name='T02-amostragem',steps=[{
            'id':f's{i}','action':'classical','request':{'config':{**config,'seed':i},'trajectories':4096,'substeps':12}}
            for i in range(5)])
        record={'steps':[{'execution_id':str(i)} for i in range(5)]}
        def load(root,state):
            return {},{'i':int(state['execution_id'])},{'quality':{'controls':[]}}
        with patch.object(study,'_load',side_effect=load),patch.object(study,'_arrays',side_effect=lambda a,p:{'psa_c3':np.array([[a['i']*.1]])}):
            result=study.analyze_phase(Path('/tmp'),spec,record)
        self.assertEqual(result['status'],'failed')
        self.assertEqual(len(result['checks']),1)
        self.assertEqual(len(result['cases']),1)
        self.assertGreater(result['checks'][0]['value'],.01)

    def test_official_classical_name_produces_metrics_and_exports_real_curves(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=service.store;service.store=RunStore(Path(temp))
            try:
                spec=protocol.ProtocolSpec(name='T03-classica-principal',steps=[{
                    'id':f's{seed}','action':'classical','request':{'config':{'n':4,'points':5,'t_max':1.,'mu':3.,'seed':seed},'trajectories':32,'substeps':4}}
                    for seed in (1,2)])
                record=protocol.run_protocol(spec)
                report=study.analyze_phase(Path(temp),spec,record,repetitions=20)
                self.assertEqual(len(report['cases']),1)
                self.assertIn('psa_analysis',report['cases'][0])
                self.assertEqual(report['cases'][0]['psa_analysis']['repetitions'],2)
                output=Path(temp)/'figures';output.mkdir()
                exported=study.export_phase(Path(temp),spec,record,output)
                self.assertEqual({p.suffix for p in exported},{'.csv','.png'})
                for file in exported:
                    self.assertGreater(file.stat().st_size,100)
            finally:
                service.store=previous

if __name__=='__main__':
    unittest.main()
