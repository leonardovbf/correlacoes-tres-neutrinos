"""Operações locais de replay: índices físicos, leitura e ruído calibrado."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel, pauli_error, thermal_relaxation_error
from qiskit_aer.noise.device import basic_device_gate_errors
from qiskit_ibm_runtime.models import BackendProperties


def compact_circuit(circuit, physical=None):
    """Remove fios ociosos sem transpilar, alterar portas ou permutar bits clássicos."""
    used=sorted({circuit.find_bit(q).index for item in circuit.data
        if item.operation.name!='barrier' for q in item.qubits})
    physical=used if physical is None else list(physical)
    if not set(used).issubset(physical):
        raise ValueError('O template passou a usar qubits fora do circuito base')
    mapping={q:k for k,q in enumerate(physical)}
    result=QuantumCircuit(len(physical),circuit.num_clbits)
    result.global_phase=circuit.global_phase
    for item in circuit.data:
        indices=[circuit.find_bit(q).index for q in item.qubits]
        if item.operation.name=='barrier':
            targets=[mapping[q] for q in indices if q in mapping]
            if targets:result.barrier(*targets)
            continue
        result.append(item.operation,[mapping[q] for q in indices],
            [circuit.find_bit(bit).index for bit in item.clbits])
    return result,physical


def measurement_map(circuit):
    """Retorna qubit compacto -> bit clássico, exigindo medições terminais completas."""
    mapping={};measured=set()
    for item in circuit.data:
        qs=[circuit.find_bit(q).index for q in item.qubits]
        if item.operation.name=='measure':
            q=qs[0];b=circuit.find_bit(item.clbits[0]).index
            if q in mapping or b in mapping.values():raise ValueError('Medições repetidas')
            mapping[q]=b;measured.add(q)
        elif item.operation.name!='barrier' and measured.intersection(qs):
            raise ValueError('O circuito contém operação após medição')
    if len(mapping)!=circuit.num_qubits or set(mapping.values())!=set(range(circuit.num_clbits)):
        raise ValueError('Esperadas medições de todos os qubits, uma vez')
    return mapping


def classical_probabilities(probabilities,mapping):
    states=np.arange(len(probabilities));labels=np.zeros(len(states),dtype=np.int64)
    for q,bit in mapping.items():labels|=((states>>q)&1)<<bit
    return np.bincount(labels,weights=np.asarray(probabilities,dtype=float),minlength=len(probabilities))


def strip_measurements(circuit):
    measurement_map(circuit)
    result=QuantumCircuit(circuit.num_qubits);result.global_phase=circuit.global_phase
    for item in circuit.data:
        if item.operation.name=='measure':continue
        result.append(item.operation,[circuit.find_bit(q).index for q in item.qubits])
    return result


def subset_properties(original,physical):
    result=copy.deepcopy(original);mapping={q:k for k,q in enumerate(physical)}
    result['qubits']=[original['qubits'][q] for q in physical]
    result['gates']=[{**gate,'qubits':[mapping[q] for q in gate['qubits']]}
        for gate in original['gates'] if all(q in mapping for q in gate['qubits'])]
    return result


def qubit_value(properties,q,name,default=None):
    for item in properties['qubits'][q]:
        if item['name']==name:return float(item['value'])
    if default is not None:return default
    raise ValueError(f'Calibração sem {name} no qubit {q}')


def readout_response(properties,mapping):
    """Canal de leitura independente assimétrico, na ordem dos bits medidos."""
    n=len(mapping);states=np.arange(1<<n)
    result=np.ones((1<<n,1<<n))
    for q,bit in mapping.items():
        p10=qubit_value(properties,q,'prob_meas1_prep0')
        p01=qubit_value(properties,q,'prob_meas0_prep1')
        source=((states>>bit)&1)[None,:];target=((states>>bit)&1)[:,None]
        result*=np.where(source==0,np.where(target==0,1-p10,p10),np.where(target==0,p01,1-p01))
    np.testing.assert_allclose(result.sum(axis=0),1,atol=1e-12)
    return result


def calibrated_gate_model(properties,circuit):
    """Canais Aer oficiais para erro de porta + relaxação durante portas, T=0.

    Usa a função pública de geração de canais: o wrapper from_backend_properties
    falha com o campo frequency ausente no snapshot Runtime. Em T=0 a população
    térmica de equilíbrio é zero, independentemente da frequência.
    """
    bp=BackendProperties.from_dict(properties)
    noise=NoiseModel(basis_gates=['rz','sx','x','cz','id'])
    channels={}
    for name,qubits,error in basic_device_gate_errors(bp,gate_error=True,thermal_relaxation=True,temperature=0):
        channels[name,tuple(qubits)]=error
        noise.add_quantum_error(error,name,qubits)
    # CZ é simétrica; alguns snapshots fornecem somente uma orientação da aresta.
    for item in circuit.data:
        name=item.operation.name;qs=tuple(circuit.find_bit(q).index for q in item.qubits)
        if name in ('cz','sx','x') and (name,qs) not in channels:
            if name=='cz' and (name,qs[::-1]) in channels:
                noise.add_quantum_error(channels[name,qs[::-1]],name,qs)
            else:
                # Um canal ideal é omitido pelo Aer; verifique a calibração em vez
                # de pressupor silenciosamente ruído zero em uma porta não medida.
                try:calibrated=bp.gate_error(name,qs)
                except Exception as exc:raise ValueError(f'Porta sem calibração: {name}{qs}') from exc
                if calibrated!=0:raise ValueError(f'Porta sem canal não ideal: {name}{qs}')
    return noise,bp


def initialization(circuit,properties):
    result=QuantumCircuit(circuit.num_qubits)
    for q in range(circuit.num_qubits):
        probability=qubit_value(properties,q,'init_error')
        if probability:result.append(pauli_error([('X',probability),('I',1-probability)]).to_instruction(),[q])
    result.compose(circuit,inplace=True)
    return result


def asap_idle_relaxation(circuit,properties,bp):
    """Sensibilidade de escalonamento ASAP; não afirma recuperar pulsos reais."""
    result=QuantumCircuit(circuit.num_qubits);result.global_phase=circuit.global_phase
    clocks=np.zeros(circuit.num_qubits);idle_total=np.zeros(circuit.num_qubits)
    def wait(q,until):
        duration=until-clocks[q]
        if duration>1e-15:
            t1=bp.t1(q);t2=min(bp.t2(q),2*t1)
            result.append(thermal_relaxation_error(t1,t2,duration,0).to_instruction(),[q])
            idle_total[q]+=duration;clocks[q]=until
    for item in circuit.data:
        name=item.operation.name;qs=[circuit.find_bit(q).index for q in item.qubits]
        if item.clbits or name=='measure':raise ValueError('Remova medições antes do escalonamento')
        start=max(clocks[qs],default=0.)
        for q in qs:wait(q,start)
        if name=='barrier':
            result.barrier(*qs);continue
        if name=='rz':duration=0.
        else:
            try:duration=bp.gate_length(name,qs)
            except Exception:
                if name=='cz':duration=bp.gate_length(name,qs[::-1])
                else:raise
        result.append(item.operation,qs)
        for q in qs:clocks[q]=start+duration
    return result,{'schedule':'assumed_ASAP','duration_seconds':float(clocks.max()),
        'idle_seconds_per_qubit':idle_total.tolist(),'not_measured_hardware_schedule':True}


def checked_density(probabilities):
    p=np.asarray(probabilities,dtype=float)
    deviation=abs(float(p.sum())-1)
    if deviation>1e-6 or p.min() < -1e-9:
        raise ValueError('Probabilidades inválidas na evolução ruidosa')
    p=np.maximum(p,0);p/=p.sum()
    return p,deviation
