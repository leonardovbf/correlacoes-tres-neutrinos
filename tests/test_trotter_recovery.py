"""Controles da emenda de discretização após a falha observada na T06."""
import json
import unittest
from pathlib import Path

from app.backend import protocol, trotter_recovery
from neutrinos.qiskit_backend import aer_step_limit


class TrotterRecoveryTests(unittest.TestCase):
    def test_amendment_is_versioned_and_keeps_thresholds(self):
        self.assertEqual(json.loads((trotter_recovery.ROOT/trotter_recovery.DOCUMENT).read_text()),
                         trotter_recovery.document())
        self.assertEqual(trotter_recovery.LIMITS, {'pe': 1e-6, 'c2': 1e-5, 'c3': 1e-5})

    def test_noise_grid_refines_only_failed_cell_and_reference(self):
        path=Path('configs/protocols/artigo_v1/06_ruido.json')
        original=protocol.read_protocol(path)
        refined,overrides=trotter_recovery.refine_spec(original)
        self.assertEqual(len(refined.steps),len(original.steps)+21)
        self.assertEqual(len(overrides),20)
        old={step.id:step for step in original.steps}
        new={step.id:step for step in refined.steps}
        for step in original.steps:
            if step.action=='classical':
                cfg=step.request['config']
                if cfg['mu']==10. and cfg['t_max']==4.:
                    self.assertEqual(new[step.id].request['config']['points'],29)
                else:
                    self.assertEqual(new[step.id],step)
            elif step.action in ('aer','mitigation') and step.id.startswith('m4_t2_'):
                self.assertEqual(new[step.id].request['interval_index'],28)
        for original_id,reference_id in overrides.items():
            self.assertEqual(new[reference_id].request['substeps'],24)
            self.assertEqual(new[original_id],old[original_id])
        self.assertEqual(new['m4_t2_s30001_ideal_qiskit_refined'].request['interval_index'],28)
        self.assertEqual(aer_step_limit(4),512)
        self.assertEqual(aer_step_limit(8),120)

    def test_mitigation_uses_same_grid_and_refined_psa(self):
        original=protocol.read_protocol(Path('configs/protocols/artigo_v1/07_mitigacao.json'))
        refined,overrides=trotter_recovery.refine_spec(original)
        self.assertFalse(overrides)
        self.assertEqual(len(refined.steps),len(original.steps))
        new={step.id:step for step in refined.steps}
        self.assertEqual(new['mit_m4_t1_s40001'].request['substeps'],24)
        self.assertEqual(new['mit_m4_t2_s40001'].request['config']['points'],29)
        self.assertEqual(new['mit_m4_t2_s40001_moderado_16384'].request['interval_index'],28)


if __name__=='__main__':
    unittest.main()
