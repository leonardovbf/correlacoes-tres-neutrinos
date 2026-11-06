"""Circuito Qiskit correspondente a um intervalo do integrador Trotter.

Este módulo é opcional: o motor numérico principal funciona sem Qiskit.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from .sim import ExperimentConfig


def aer_step_limit(n: int) -> int:
    """Grade refinada de quatro qubits; mantém o limite dos sistemas maiores."""
    return 512 if n <= 4 else 120


def build_trotter_circuit(config: ExperimentConfig, interval: float, steps: int):
    """Prepara o estado e aplica Suzuki–Trotter simétrico de 2ª ordem.

    Cada termo de um qubit e cada produto Heisenberg de um par é evoluído
    exatamente dentro de cada subpasso; os termos de pares distintos são
    compostos simetricamente.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate

    if config.n > 8 or not 1 <= steps <= 4096:
        raise ValueError("Circuito Qiskit: 2–8 qubits e 1–4096 passos")
    circuit = QuantumCircuit(config.n)
    for i, (x0, y0, z0) in enumerate(config.initial_bloch):
        if np.isclose(z0, -1.0):
            circuit.x(i)
        elif not np.isclose(z0, 1.0):
            circuit.ry(float(np.arccos(np.clip(z0, -1, 1))), i)
            circuit.rz(float(np.arctan2(y0, x0)), i)

    identity = np.eye(2, dtype=np.complex128)
    x = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    z = np.diag([1, -1]).astype(np.complex128)
    bx, by, bz = config.b_field
    pauli_dot = np.kron(x, x) + np.kron(y, y) + np.kron(z, z)
    dt = interval / steps
    one_gates = []
    for i, omega in enumerate(config.omega):
        angle = omega * dt / 4  # metade de um subpasso para H_i = omega B.sigma/2
        u = np.cos(angle) * identity - 1j * np.sin(angle) * (bx * x + by * y + bz * z)
        one_gates.append(UnitaryGate(u, label=f"V{i}"))
    pairs = [tuple(map(int, pair)) for pair in config.pair_index]
    g = config.g_matrix
    pair_gates = {(i, j): UnitaryGate(expm(-1j * (config.mu * g[i, j] * dt / (8 * config.n)) * pauli_dot), label=f"ν{i}{j}")
                  for i, j in pairs}
    for _ in range(steps):
        for i, gate in enumerate(one_gates):
            circuit.append(gate, [i])
        for i, j in pairs:
            circuit.append(pair_gates[(i, j)], [i, j])
        for i, j in reversed(pairs):
            circuit.append(pair_gates[(i, j)], [i, j])
        for i in reversed(range(config.n)):
            circuit.append(one_gates[i], [i])
    return circuit


def first_interval_probabilities(config: ExperimentConfig, steps: int, interval_index: int = 1):
    from qiskit.quantum_info import Statevector

    if not 1 <= interval_index < config.points:
        raise ValueError("Instante fora da grade")
    interval = float(config.times[interval_index])
    circuit = build_trotter_circuit(config, interval, steps * interval_index)
    return circuit, np.asarray(Statevector.from_instruction(circuit).probabilities())


def simulate_gate_noise(config: ExperimentConfig, interval_index: int, steps_per_interval: int,
                        shots: int, single_qubit_error: float, two_qubit_error: float,
                        readout_error: float, *, calibration_state: int | None = None,
                        seed_offset: int = 0) -> tuple[np.ndarray, dict]:
    """Executa um instante em Aer com ruído despolarizante e de leitura.

    O modelo é exploratório e não representa uma calibração de hardware IBM.
    """
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

    limit = aer_step_limit(config.n)
    if not 1 <= interval_index < config.points or interval_index * steps_per_interval > limit:
        raise ValueError(f"Instante ou profundidade fora do limite Aer ({limit} passos)")
    if not 32 <= shots <= 20000:
        raise ValueError("shots fora do intervalo permitido")
    for name, probability in (("single_qubit_error", single_qubit_error),
                              ("two_qubit_error", two_qubit_error), ("readout_error", readout_error)):
        if not 0 <= probability <= .25:
            raise ValueError(f"{name} deve estar entre 0 e 0,25")

    if calibration_state is None:
        circuit = build_trotter_circuit(config, float(config.times[interval_index]),
                                        interval_index * steps_per_interval)
    else:
        from qiskit import QuantumCircuit
        if calibration_state not in (0, 1):
            raise ValueError("Calibração aceita somente todos 0 ou todos 1")
        circuit = QuantumCircuit(config.n)
        if calibration_state:
            circuit.x(range(config.n))
    basis = ["rz", "sx", "x", "cx"]
    compiled = transpile(circuit, basis_gates=basis, optimization_level=1,
                         seed_transpiler=config.seed)
    compiled.measure_all()
    noise = NoiseModel()
    if single_qubit_error:
        noise.add_all_qubit_quantum_error(depolarizing_error(single_qubit_error, 1), ["sx", "x"])
    if two_qubit_error:
        noise.add_all_qubit_quantum_error(depolarizing_error(two_qubit_error, 2), "cx")
    if readout_error:
        noise.add_all_qubit_readout_error(ReadoutError([[1-readout_error, readout_error],
                                                       [readout_error, 1-readout_error]]))
    simulator = AerSimulator(noise_model=noise, basis_gates=basis, method="density_matrix")
    seed = config.seed + 200_000 + seed_offset
    result = simulator.run(compiled, shots=shots, seed_simulator=seed).result()
    counts = np.zeros(1 << config.n, dtype=np.int64)
    for bitstring, count in result.get_counts().items():
        counts[int(bitstring.replace(" ", ""), 2)] = count
    return counts, {"time_index": interval_index, "tau": float(config.times[interval_index]),
                    "steps_per_interval": steps_per_interval,
                    "total_trotter_steps": interval_index * steps_per_interval,
                    "shots": shots, "single_qubit_depolarizing": single_qubit_error,
                    "two_qubit_depolarizing": two_qubit_error,
                    "readout_bit_flip": readout_error,
                    "transpiled_depth": compiled.depth(), "cx_count": int(compiled.count_ops().get("cx", 0)),
                    "seed_transpiler": config.seed, "optimization_level": 1,
                    "seed_simulator": seed, "calibration_state": calibration_state,
                    "noise_scope": "Aer: despolarização em sx/x/cx e erro de leitura independente"}
