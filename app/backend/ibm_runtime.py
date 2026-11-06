"""Conexão opcional com hardware IBM Quantum via Qiskit Runtime.

A credencial fica somente no processo Python. Nenhuma função deste módulo
inclui a chave em respostas, logs ou arquivos de experimento.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import json
import os
from contextlib import contextmanager
from contextvars import ContextVar

import numpy as np
from dotenv import load_dotenv

from neutrinos.qiskit_backend import build_trotter_circuit
from neutrinos.sim import ExperimentConfig

from .schemas import HardwareRequest
from .storage import ROOT


load_dotenv(ROOT / ".env", override=False)
_active_service = ContextVar("ibm_active_service", default=None)


@contextmanager
def shared_session():
    """Reutiliza um cliente real numa consulta em lote; não persiste credenciais extras."""
    client = _service()
    token = _active_service.set(client)
    try:
        yield client
    finally:
        _active_service.reset(token)


def status() -> dict:
    return {
        "configured": bool(os.environ.get("IBM_QUANTUM_API_KEY", "").strip()),
        "sdk_installed": importlib.util.find_spec("qiskit_ibm_runtime") is not None,
        "instance_configured": bool(os.environ.get("IBM_QUANTUM_INSTANCE", "").strip()),
        "preferred_backend": os.environ.get("IBM_QUANTUM_BACKEND", "").strip() or None,
    }


def _service():
    active = _active_service.get()
    if active is not None:
        return active
    if not status()["configured"]:
        raise ValueError("Preencha IBM_QUANTUM_API_KEY no arquivo .env da raiz e reinicie o backend")
    if not status()["sdk_installed"]:
        raise RuntimeError("Instale as dependências Qiskit: pip install -e '.[qiskit]'")
    from qiskit_ibm_runtime import QiskitRuntimeService

    options = {"channel": "ibm_quantum_platform", "token": os.environ["IBM_QUANTUM_API_KEY"]}
    instance = os.environ.get("IBM_QUANTUM_INSTANCE", "").strip()
    if instance:
        options["instance"] = instance
    try:
        return QiskitRuntimeService(**options)
    except Exception as exc:
        raise RuntimeError("Não foi possível autenticar na IBM Quantum. Confira a chave e a instância no .env") from exc


def list_backends(min_qubits: int = 2) -> list[dict]:
    if not 2 <= min_qubits <= 8:
        raise ValueError("A seleção de hardware aceita entre 2 e 8 qubits")
    try:
        backends = _service().backends(min_num_qubits=min_qubits, simulator=False, operational=True)
        return sorted(({"name": backend.name, "num_qubits": backend.num_qubits}
                       for backend in backends), key=lambda item: item["name"])
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Não foi possível listar os dispositivos IBM Quantum disponíveis") from exc


def submit(config: ExperimentConfig, request: HardwareRequest) -> dict:
    if config.n > 8 or request.interval_index >= config.points:
        raise ValueError("Instante ou número de qubits fora do cenário")
    if request.interval_index * request.steps > 120:
        raise ValueError("Hardware limitado a 120 subpassos Trotter por execução")
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit import qpy
    from qiskit_ibm_runtime.executor_sampler import Sampler

    try:
        service = _service()
        backend = service.backend(request.backend)
        if backend.num_qubits < config.n or getattr(backend.configuration(), "simulator", False):
            raise ValueError("Selecione um dispositivo quântico real com qubits suficientes")
        if not backend.status().operational:
            raise ValueError("O dispositivo selecionado não está operacional")
        if request.role.startswith("calibration"):
            from qiskit import QuantumCircuit
            if request.initial_layout is None:
                raise ValueError("A calibração exige os qubits físicos da medição de sinal")
            circuit = QuantumCircuit(config.n)
            if request.role == "calibration_one":
                circuit.x(range(config.n))
        else:
            circuit = build_trotter_circuit(config, float(config.times[request.interval_index]),
                                            request.interval_index * request.steps)
        circuit.measure_all()
        transpiler_seed = request.transpiler_seed if request.transpiler_seed is not None else config.seed
        manager = generate_preset_pass_manager(backend=backend, optimization_level=1,
                                               seed_transpiler=transpiler_seed,
                                               initial_layout=request.initial_layout)
        isa_circuit = manager.run(circuit)
        if isa_circuit.depth() > request.max_depth:
            raise ValueError("Profundidade após transpilar ultrapassa max_depth; nenhum job foi enviado")
        serialized = io.BytesIO()
        qpy.dump(isa_circuit, serialized)
        circuit_bytes = serialized.getvalue()
        properties = backend.properties() if hasattr(backend, "properties") else None
        calibration = json.loads(json.dumps(properties.to_dict(), default=str)) if properties else None
        job = Sampler(mode=backend).run([isa_circuit], shots=request.shots)
        return {"job_id": job.job_id(), "backend": backend.name,
                "circuit_qpy_base64": base64.b64encode(circuit_bytes).decode("ascii"),
                "circuit_sha256": hashlib.sha256(circuit_bytes).hexdigest(),
                "transpilation": {"optimization_level": 1, "seed_transpiler": transpiler_seed,
                                  "physical_qubits": isa_circuit.layout.final_index_layout()},
                "runtime_options": {"primitive": "Sampler", "shots": request.shots},
                "role": request.role,
                "backend_properties": calibration,
                "transpiled_depth": isa_circuit.depth(),
                "two_qubit_gates": sum(count for gate, count in isa_circuit.count_ops().items()
                                       if gate in {"cx", "cz", "ecr", "rzz", "rxx", "ryy"})}
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Falha ao enviar o circuito à IBM Quantum. Confira a conta, o backend e os limites do plano") from exc


def fetch(job_id: str, n: int) -> tuple[str, np.ndarray | None]:
    try:
        job = _service().job(job_id)
        raw_status = job.status()
        state = str(getattr(raw_status, "value", raw_status)).upper()
        if state != "DONE":
            return state, None
        result = job.result()
        observed = result[0].data.meas.get_counts()
        counts = np.zeros(1 << n, dtype=np.int64)
        for bitstring, count in observed.items():
            position = int(str(bitstring).replace(" ", ""), 2)
            if position >= len(counts):
                raise ValueError("Resultado IBM com número inesperado de bits")
            counts[position] = count
        return state, counts
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Não foi possível consultar o job IBM Quantum") from exc
