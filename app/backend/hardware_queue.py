"""Aquisição IBM antecipada, explicitamente separada da validação científica local."""
from __future__ import annotations
import io
import json
from pathlib import Path
import numpy as np
from neutrinos.sim import ExperimentConfig,classical_exact,quantum_trotter
from neutrinos.qiskit_backend import build_trotter_circuit
from . import audit,ibm_runtime,protocol,service,study


def config(seed):
    return {'n':4,'mu':3.,'theta':.2,'t_max':2.,'points':8,'seed':seed,'flavors':[0,0,1,1],
        'omega_values':[.7,.9,1.1,1.3],'g_values':(np.ones((4,4))-np.eye(4)).tolist()}


def prepare(source_study,backend,*,max_depth=20000,progress=print):
    from qiskit import qpy
    from qiskit.transpiler import generate_preset_pass_manager
    root=service.store.root.resolve();source_study=source_study.resolve()
    source=json.loads(source_study.read_text())
    if source_study.parents[2]!=root or source['profile']!='official-v1-r2':
        raise ValueError('Use um estudo oficial no mesmo --output')
    if backend not in {b['name'] for b in ibm_runtime.list_backends(4)}:
        raise ValueError('Backend indisponível na conta')
    cloud=ibm_runtime._service();target=cloud.backend(backend)
    if not target.status().operational:
        raise ValueError('Backend não operacional')
    cfg=ExperimentConfig.from_dict(config(60001))
    exact=classical_exact(cfg);trials=[];selected=None
    for steps in (1,2,4,8,16):
        ideal,_=quantum_trotter(cfg,steps,32,0.)
        error=float(np.max(np.abs(exact.c3-ideal.c3)))
        trials.append({'steps_per_interval':steps,'total_steps':7*steps,'max_c3_error':error})
        if selected is None and error<=.001:
            selected=(steps,error)
    if selected is None:
        raise ValueError('Precisão ideal insuficiente para enviar o circuito')
    steps_per_interval,residual=selected
    progress('Conferindo profundidade do circuito no backend '+backend)
    circuit=build_trotter_circuit(cfg,2.,7*steps_per_interval);circuit.measure_all()
    compiled=generate_preset_pass_manager(backend=target,optimization_level=1,seed_transpiler=60001).run(circuit)
    if compiled.depth()>max_depth:
        raise ValueError(f'Profundidade {compiled.depth()} excede max_depth={max_depth}; nenhum job enviado')
    initial_layout=compiled.layout.initial_index_layout(filter_ancillas=True)
    folder=root/'hardware-queues'/audit.new_id();folder.mkdir(parents=True)
    binary=io.BytesIO();qpy.dump(compiled,binary)
    (folder/'circuit_preview.qpy').write_bytes(binary.getvalue())
    steps=[]
    for seed in range(60001,60021):
        parent=f'ibm_s{seed}'
        steps.extend([{'id':parent,'action':'classical','request':{'config':config(seed),'trajectories':4096,'substeps':12}},
            {'id':parent+'_ideal','action':'quantum','run_from':parent,'request':{'steps':steps_per_interval,'shots':32,'readout_error':0.}}])
        if seed==60001:
            steps.append({'id':'qiskit_primary','action':'circuit','run_from':parent,'request':{'steps':steps_per_interval,'interval_index':7}})
        for role,shots in (('raw',16384),('signal',12288),('calibration_zero',2048),('calibration_one',2048)):
            steps.append({'id':f'{parent}_{role}','action':'hardware','run_from':parent,'request':{
                'backend':backend,'interval_index':7,'steps':steps_per_interval,'shots':shots,'kind':'c3','index':0,
                'role':role,'calibration_reference':role.startswith('calibration'),'max_depth':max_depth,
                'transpiler_seed':60001,'initial_layout':None if role.startswith('calibration') else initial_layout}})
    spec=protocol.ProtocolSpec(name='T08-aquisicao-antecipada',steps=steps,description=(
        'Aquisição solicitada durante recuperação local. Ponto principal fixo N4/mu3/trio012/tau2. '
        '80 jobs, 655360 shots totais, incluindo calibração. Contagens provisórias: '
        'nenhuma conclusão H2 ou resultado oficial antes da validação amostral e T07. '
        'Passos escolhidos antes do hardware: menor valor em 1/2/4/8/16 que satisfaz erro ideal máximo K3 <=0.001. '
        'Calibração usa os mesmos qubits físicos finais do sinal.'))
    destination=folder/'protocol.json';audit.atomic_json(destination,spec.model_dump(mode='json'))
    environment=audit.environment()
    queue={'schema_version':1,'status':'prepared','started_utc':audit.utc_now(),'backend':backend,
        'source_study':str(source_study),'source_study_sha256':audit.file_hash(source_study),
        'protocol':{'path':destination.name,'sha256':audit.file_hash(destination)},
        'environment':environment,'source_snapshot':audit.archive_environment(root,environment),
        'scientific_status':'provisional_pending_local_precision_and_T07',
        'requested_by':'Solicitação explícita de executar a parte quântica ou colocá-la na fila durante a recuperação.',
        'planned_jobs':80,'total_requested_shots':655360,'shots_per_method':327680,
        'ideal_max_c3_error':residual,'ideal_error_limit':.001,
        'trotter_selection':{'rule':'Menor número em 1/2/4/8/16 por intervalo com erro máximo K3 <=0.001 em todos os tempos/trios, antes de observar contagens IBM.',
            'selected_steps_per_interval':steps_per_interval,'total_steps':7*steps_per_interval,'trials':trials,
            'scope':'O hardware usa discretização própria validada; não representa o mesmo circuito profundo do perfil Aer T06/T07.'},
        'preview':{'depth':compiled.depth(),'two_qubit_gates':sum(v for k,v in compiled.count_ops().items() if k in ('cx','cz','ecr','rzz')),
            'initial_layout':initial_layout,'fixed_transpiler_seed':60001,
            'physical_qubits':compiled.layout.final_index_layout(),'qpy_sha256':audit.file_hash(folder/'circuit_preview.qpy')},
        'max_depth':max_depth,'protocol_record':None}
    path=folder/'queue.json';audit.atomic_json(path,queue)
    return {'queue_record':str(path),'backend':backend,'planned_jobs':80,'total_requested_shots':655360,
        'depth':compiled.depth(),'ideal_max_c3_error':residual}


def enqueue(path,*,allow_hardware=False,progress=print):
    if not allow_hardware:
        raise ValueError('Envio real exige --allow-hardware')
    path=path.resolve();root=service.store.root.resolve()
    if path.parent.parent!=root/'hardware-queues':
        raise ValueError('Use o mesmo --output da preparação')
    queue=json.loads(path.read_text())
    if audit.environment_differences(queue['environment']):
        raise ValueError('Fontes/dependências mudaram desde a preparação da fila')
    file=path.parent/queue['protocol']['path']
    if audit.file_hash(file)!=queue['protocol']['sha256']:
        raise ValueError('Protocolo da fila foi alterado')
    def registered(record):
        queue.update(status='submitting',protocol_record=str(record.resolve()))
        audit.atomic_json(path,queue)
    try:
        result=protocol.run_protocol(protocol.read_protocol(file),
            resume=Path(queue['protocol_record']) if queue.get('protocol_record') else None,
            allow_hardware=True,progress=progress,on_record=registered,step_validator=study.validate_step)
        queue['status']='submitted'
    except BaseException as exc:
        queue.update(status='submission_incomplete',error=audit.safe_error(exc));raise
    finally:
        queue['last_update_utc']=audit.utc_now();audit.atomic_json(path,queue)
    return {'status':queue['status'],'queue_record':str(path),'protocol_record':queue['protocol_record'],
        'submitted_jobs':sum(s['action']=='hardware' and s['status']=='completed' for s in result['steps'])}
