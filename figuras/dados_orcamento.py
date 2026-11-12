"""Dados da figura do orçamento de medições (circuitos ideais, C3 contra o exato).

1. Reproduz a fase T05 com as mesmas sementes (20001–20020, 16 passos de Trotter
   por intervalo) e confere o RMSE com o pacote de resultados do artigo.
2. Estima a variabilidade do RMSE repetindo o experimento inteiro com sementes
   novas. Agregar 20 blocos de m medições equivale a uma multinomial com 20m
   medições, pois os momentos são lineares nas frequências e os cumulantes são
   calculados após a agregação. Não usa bootstrap.

Uso: PYTHONPATH=src python figuras/dados_orcamento.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

from neutrinos.sim import (ExperimentConfig, _moments_from_probabilities, classical_exact,
                           quantum_trotter, trotter_probabilities)
from neutrinos.study_analysis import pooled

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "figuras" / "dados" / "orcamento_medicoes.csv"
PACOTE = next((RAIZ / "analysis" / "article_packages").glob("*/tables/measurement_budget.csv"))

TAMANHOS = (4, 6, 8)
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0)
ORCAMENTOS = (1024, 4096, 16384)
BLOCOS = 20
SEMENTES = range(20001, 20001 + BLOCOS)
PASSOS = 16
REPLICACOES = 500


def configuracao(n: int, mu: float, seed: int) -> ExperimentConfig:
    return ExperimentConfig(n=n, mu=mu, theta=0.2, t_max=10.0, points=201, seed=seed,
                            flavors=tuple([0] * (n // 2) + [1] * (n // 2)),
                            omega_values=tuple(0.7 + 0.6 * i / (n - 1) for i in range(n)))


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - b) ** 2)))


def main() -> None:
    pacote = {(int(r["n"]), float(r["mu"]), int(r["shots_per_block"])): float(r["k3_rmse"])
              for r in csv.DictReader(PACOTE.open())}
    linhas = []
    for n in TAMANHOS:
        for mu in LAMBDAS:
            base = configuracao(n, mu, 20001)
            exato = classical_exact(base).c3
            dados = trotter_probabilities(base, PASSOS)
            prob = np.clip(dados[0], 0, None)
            prob /= prob.sum(axis=1, keepdims=True)
            rng = np.random.default_rng(910_000 + 100 * n + int(10 * mu))
            for m in ORCAMENTOS:
                blocos = []
                for seed in SEMENTES:
                    _, medido = quantum_trotter(configuracao(n, mu, seed), PASSOS, m,
                                                probability_data=dados)
                    blocos.append({"m1": medido.m1, "m2": medido.m2, "m3": medido.m3})
                observado = rmse(pooled(blocos, n)[1], exato)
                referencia = pacote[(n, mu, m)]
                if not np.isclose(observado, referencia, rtol=1e-9, atol=1e-12):
                    sys.exit(f"Reprodução diverge do pacote em N={n}, λ={mu}, m={m}: "
                             f"{observado} != {referencia}")
                total = BLOCOS * m
                replicas = []
                for _ in range(REPLICACOES):
                    freq = rng.multinomial(total, prob) / total
                    replicas.append(rmse(_moments_from_probabilities(base, freq, "", {}).c3, exato))
                baixo, mediana, alto = np.quantile(replicas, [0.025, 0.5, 0.975])
                linhas.append({"n": n, "mu": mu, "medicoes_por_bloco": m, "blocos": BLOCOS,
                               "rmse_c3": observado, "rmse_c3_mediana": mediana,
                               "rmse_c3_p025": baixo, "rmse_c3_p975": alto,
                               "replicacoes": REPLICACOES})
                print(f"N={n} λ={mu:>4} m={m:>5}: RMSE={observado:.3e} "
                      f"faixa95=[{baixo:.3e}; {alto:.3e}]", flush=True)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
