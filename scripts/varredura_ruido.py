"""Varredura de ruído para H2: a mitigação de leitura amplia o limiar de ruído?

Caso principal (N=4, λ=3, τ=2, trio 0-1-2), Trotter simétrico com o menor número de
passos que respeita |ΔC3| ≤ 10⁻³ (12). Grade 2D: despolarização de dois qubits p
(um qubit: p/10) × erro de leitura simétrico ε. Orçamento por método M = 20 × 16.384;
o mitigado usa 3m/4 no sinal e m/8 em cada calibração, como no artigo.

O Aer (matriz densidade) dá a distribuição com ruído de portas; o erro de leitura é
aplicado como produto tensorial de matrizes de inversão, como no ReadoutError do Aer,
e as contagens são amostradas por multinomial. A análise é a função h2 do estudo.

Uso: PYTHONPATH=src python scripts/varredura_ruido.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from neutrinos.qiskit_backend import build_trotter_circuit
from neutrinos.sim import ExperimentConfig, classical_exact, phase_space
from neutrinos.study_analysis import h2

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "figuras" / "dados" / "varredura_ruido.csv"
MU, TAU, PASSOS = 3.0, 2.0, 12
BLOCOS, M = 20, 16384
ERROS_PORTA = (0.0, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3)
ERROS_LEITURA = (0.0, 0.005, 0.01, 0.02, 0.03, 0.05)


def configuracao(seed: int) -> ExperimentConfig:
    return ExperimentConfig(n=4, mu=MU, theta=0.2, t_max=TAU, points=8, seed=seed,
                            flavors=(0, 0, 1, 1), omega_values=(0.7, 0.9, 1.1, 1.3))


def distribuicoes(p2: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Probabilidades sem leitura: sinal, calibração |0000⟩ e |1111⟩."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    base = ["rz", "sx", "x", "cx"]
    ruido = NoiseModel(basis_gates=base)
    if p2:
        ruido.add_all_qubit_quantum_error(depolarizing_error(p2 / 10, 1), ["sx", "x"])
        ruido.add_all_qubit_quantum_error(depolarizing_error(p2, 2), "cx")
    simulador = AerSimulator(method="density_matrix", noise_model=ruido, basis_gates=base)
    sinal = build_trotter_circuit(configuracao(30001), TAU, PASSOS)
    um = QuantumCircuit(4)
    um.x(range(4))
    saidas = []
    for circuito in (sinal, QuantumCircuit(4), um):
        compilado = transpile(circuito, basis_gates=base, optimization_level=1, seed_transpiler=30001)
        compilado.save_probabilities()
        saidas.append(np.asarray(simulador.run(compilado).result().data()["probabilities"]))
    return tuple(np.clip(s, 0, None) / np.clip(s, 0, None).sum() for s in saidas)


def leitura(probabilidades: np.ndarray, epsilon: float) -> np.ndarray:
    matriz = np.array([[1 - epsilon, epsilon], [epsilon, 1 - epsilon]])
    total = np.array([[1.0]])
    for _ in range(4):
        total = np.kron(total, matriz)
    return total @ probabilidades


def main() -> None:
    from qiskit.quantum_info import Statevector
    from neutrinos.mitigation import observable

    exato = float(classical_exact(configuracao(30001)).c3[-1, 0])
    ideal = Statevector.from_instruction(build_trotter_circuit(configuracao(30001), TAU, PASSOS))
    residuo = abs(observable(np.asarray(ideal.probabilities()), "c3", (0, 1, 2)) - exato) + 1e-5
    psa = []
    for seed in range(40001, 40001 + BLOCOS):  # mesmas sementes da fase de mitigação (Tabela 5)
        serie = phase_space(configuracao(seed), trajectories=4096, substeps=12)
        psa.append({"m1": serie.m1[-1], "m2": serie.m2[-1], "m3": serie.m3[-1]})
    print(f"exato={exato:.6f}  resíduo Trotter+numérico={residuo:.2e}", flush=True)

    linhas = []
    rng = np.random.default_rng(73001)
    for p2 in ERROS_PORTA:
        sinal, zero, um = distribuicoes(p2)
        for epsilon in ERROS_LEITURA:
            s, z, u = (leitura(x, epsilon) for x in (sinal, zero, um))
            blocos = [{"raw": rng.multinomial(M, s), "signal": rng.multinomial(3 * M // 4, s),
                       "zero": rng.multinomial(M // 8, z), "one": rng.multinomial(M // 8, u)}
                      for _ in range(BLOCOS)]
            resultado = h2(blocos, psa, exato, residuo, repetitions=2000, seed=72001)
            if resultado["status"] != "analyzed":
                print(f"p={p2:g} ε={epsilon:g}: {resultado['status']}", flush=True)
                continue
            for metodo, v in resultado["methods"].items():
                linhas.append({"erro_porta": p2, "erro_leitura": epsilon, "metodo": metodo,
                               "estimativa": v["estimate"], "exato": exato, "psa": resultado["psa"],
                               "dif_exato_low": v["difference_exact_ci95_with_residual"][0],
                               "dif_exato_high": v["difference_exact_ci95_with_residual"][1],
                               "dif_psa_low": v["difference_psa_ci95"][0],
                               "dif_psa_high": v["difference_psa_ci95"][1],
                               "resolve": v["resolves"]})
            bruto, mitigado = (resultado["methods"][k] for k in ("raw", "mitigated"))
            print(f"p={p2:<7g} ε={epsilon:<6g} bruto={bruto['estimate']:+.4f} ({'ok' if bruto['resolves'] else '--'})"
                  f"  mitigado={mitigado['estimate']:+.4f} ({'ok' if mitigado['resolves'] else '--'})", flush=True)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
