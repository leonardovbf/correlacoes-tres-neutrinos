"""Controles de mapeamento e canais físicos usados no replay pareado."""
import sys
import unittest
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'analysis')]
from paired_aer_common import (compact_circuit,measurement_map,classical_probabilities,
    readout_response,calibrated_gate_model,initialization,asap_idle_relaxation,strip_measurements)


def calibration():
    date='2026-11-07T12:00:00+00:00'
    def value(name,v,unit=''):return {'name':name,'value':v,'unit':unit,'date':date}
    qubits=[[value('T1',100,'ns'),value('T2',150,'ns'),value('init_error',.02),
        value('prob_meas1_prep0',.1),value('prob_meas0_prep1',.2)] for _ in range(2)]
    gates=[]
    for name,qs,length,error in [('sx',[0],30,.001),('sx',[1],30,.001),('x',[0],30,.001),('cz',[0,1],40,.01)]:
        gates.append({'gate':name,'name':name+'_'.join(map(str,qs)),'qubits':qs,
            'parameters':[value('gate_length',length,'ns'),value('gate_error',error)]})
    return {'backend_name':'local_fixture','backend_version':'1.0.0','last_update_date':date,
        'qubits':qubits,'gates':gates,'general':[],'general_qlists':{}}


class PairedAerTests(unittest.TestCase):
    def test_compaction_preserves_classical_order_with_nonconsecutive_physical_qubits(self):
        circuit=QuantumCircuit(10,2);circuit.x(7);circuit.sx(2);circuit.cz(2,7)
        circuit.measure(7,0);circuit.measure(2,1)
        compact,physical=compact_circuit(circuit)
        self.assertEqual(physical,[2,7])
        actual=classical_probabilities(Statevector.from_instruction(strip_measurements(compact)).probabilities(),measurement_map(compact))
        np.testing.assert_allclose(actual,[0,.5,0,.5],atol=1e-14)

    def test_readout_channel_respects_asymmetry_and_measurement_permutation(self):
        props=calibration();props['qubits'][1][3]['value']=.3;props['qubits'][1][4]['value']=.4
        matrix=readout_response(props,{0:1,1:0})
        q0=np.array([[.9,.2],[.1,.8]]);q1=np.array([[.7,.4],[.3,.6]])
        np.testing.assert_allclose(matrix,np.kron(q0,q1),atol=1e-14)

    def test_missing_frequency_is_supported_at_zero_temperature(self):
        circuit=QuantumCircuit(2);circuit.sx(0);circuit.cz(0,1)
        model,_=calibrated_gate_model(calibration(),circuit)
        self.assertIn('cz',model.noise_instructions)
        self.assertIn('sx',model.noise_instructions)

    def test_idle_relaxation_has_expected_excited_state_survival(self):
        props=calibration();circuit=QuantumCircuit(2);circuit.x(0)
        for _ in range(5):circuit.sx(1)
        circuit.barrier()
        _,bp=calibrated_gate_model(props,circuit)
        scheduled,meta=asap_idle_relaxation(circuit,props,bp)
        scheduled.save_density_matrix()
        density=np.asarray(AerSimulator(method='density_matrix').run(scheduled,shots=1).result().data(0)['density_matrix'])
        excited=float(np.diag(density).real[[1,3]].sum())
        self.assertAlmostEqual(excited,np.exp(-1.2),places=12)
        self.assertAlmostEqual(meta['idle_seconds_per_qubit'][0],120e-9,places=15)

    def test_initialization_uses_archived_reset_error(self):
        circuit=initialization(QuantumCircuit(2),calibration());circuit.save_density_matrix()
        density=np.asarray(AerSimulator(method='density_matrix').run(circuit,shots=1).result().data(0)['density_matrix'])
        self.assertAlmostEqual(float(np.diag(density).real[[1,3]].sum()),.02,places=12)

    def test_nonterminal_measurement_is_rejected(self):
        circuit=QuantumCircuit(1,1);circuit.measure(0,0);circuit.x(0)
        with self.assertRaisesRegex(ValueError,'após medição'):measurement_map(circuit)


if __name__=='__main__':unittest.main()
