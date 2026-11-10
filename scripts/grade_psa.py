"""Regenera a grade clássica do artigo (exato + 20 blocos PSA) e aplica H1 corrigida.

Mesmas configurações e sementes das fases T03 (principal: N=4,6,8; extensão: N=12,16;
λ = 0,1; 0,3; 1; 3; 10; sementes 10001–10020; 4.096 trajetórias e 12 subpassos RK4).
Cada bloco é gravado em results/psa_grade/ ao terminar; a execução é retomável.

Uso:
  PYTHONPATH=src python scripts/grade_psa.py gerar [--processos 8]
  PYTHONPATH=src python scripts/grade_psa.py analisar
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "results" / "psa_grade"
SAIDA = RAIZ / "figuras" / "dados"
TAMANHOS = (4, 6, 8, 12, 16)
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0)
SEMENTES = tuple(range(10001, 10021))
TRAJETORIAS, SUBPASSOS = 4096, 12


def configuracao(n: int, mu: float, seed: int):
    from neutrinos.sim import ExperimentConfig
    return ExperimentConfig(n=n, mu=mu, theta=0.2, t_max=10.0, points=201, seed=seed,
                            flavors=tuple([0] * (n // 2) + [1] * (n // 2)),
                            omega_values=tuple(0.7 + 0.6 * i / (n - 1) for i in range(n)))


def arquivo(n: int, mu: float, seed: int | None) -> Path:
    nome = "exato" if seed is None else f"psa_{seed}"
    return CACHE / f"n{n}_mu{mu:g}" / f"{nome}.npz"


def tarefa(n: int, mu: float, seed: int | None) -> str:
    from neutrinos.sim import classical_exact, phase_space
    destino = arquivo(n, mu, seed)
    if destino.exists():
        return f"já existe {destino.relative_to(RAIZ)}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    if seed is None:
        serie = classical_exact(configuracao(n, mu, 10001))
        dados = {"c2": serie.c2, "c3": serie.c3, "m1": serie.m1}
    else:
        serie = phase_space(configuracao(n, mu, seed), trajectories=TRAJETORIAS, substeps=SUBPASSOS)
        dados = {"m1": serie.m1, "m2": serie.m2, "m3": serie.m3}
    temporario = destino.with_suffix(".tmp.npz")
    np.savez_compressed(temporario, **dados)
    temporario.replace(destino)
    return f"N={n} λ={mu:g} {'exato' if seed is None else seed}: {time.time() - inicio:.0f}s"


def gerar(processos: int) -> None:
    tarefas = [(n, mu, s) for n in sorted(TAMANHOS, reverse=True) for mu in LAMBDAS
               for s in (None, *SEMENTES) if not arquivo(n, mu, s).exists()]
    print(f"{len(tarefas)} tarefas pendentes, {processos} processos", flush=True)
    with ProcessPoolExecutor(processos) as executor:
        futuros = [executor.submit(tarefa, *t) for t in tarefas]
        for feito, futuro in enumerate(as_completed(futuros), 1):
            print(f"[{feito}/{len(tarefas)}] {futuro.result()}", flush=True)


def analisar(repeticoes: int = 2000) -> None:
    from neutrinos.study_analysis import h1
    linhas, sorteios = [], {}
    for n in TAMANHOS:
        for mu in LAMBDAS:
            caminhos = [arquivo(n, mu, s) for s in (None, *SEMENTES)]
            if not all(c.exists() for c in caminhos):
                print(f"N={n} λ={mu:g}: incompleto, ignorado", flush=True)
                continue
            exato = np.load(caminhos[0])
            blocos = [dict(np.load(c)) for c in caminhos[1:]]
            r = h1(blocos, exato["c2"], exato["c3"], n, repetitions=repeticoes)
            k = r["noise_corrected"]
            linhas.append({
                "n": n, "mu": mu, "blocks": len(blocos),
                "r2_bruto": r["c2"]["normalized_rmse"], "r3_bruto": r["c3"]["normalized_rmse"],
                "d_bruto": r["c3"]["normalized_rmse"] - r["c2"]["normalized_rmse"],
                "ci95_bruto_low": r["r3_minus_r2_ci95"][0], "ci95_bruto_high": r["r3_minus_r2_ci95"][1],
                "r2": k["c2"]["normalized_rmse"], "r3": k["c3"]["normalized_rmse"],
                "r3_minus_r2": k["r3_minus_r2"], "ci95_low": k["r3_minus_r2_ci95"][0],
                "ci95_high": k["r3_minus_r2_ci95"][1],
                "ruido_c2": k["c2"]["noise_rms"], "ruido_c3": k["c3"]["noise_rms"],
                "sinal_c2": k["c2"]["signal_rms"], "sinal_c3": k["c3"]["signal_rms"],
                "ruido_dominante": k["c2"]["noise_dominated"] or k["c3"]["noise_dominated"],
            })
            sorteios[(n, mu)] = (k["r3_minus_r2"], k["bootstrap_reference"],
                                 np.asarray(k["r3_minus_r2_bootstrap"]))
            print(f"N={n} λ={mu:g}: D bruto={linhas[-1]['d_bruto']:.3f} "
                  f"[{linhas[-1]['ci95_bruto_low']:.3f}; {linhas[-1]['ci95_bruto_high']:.3f}] | "
                  f"D corrigido={k['r3_minus_r2']:.3f} [{k['r3_minus_r2_ci95'][0]:.3f}; "
                  f"{k['r3_minus_r2_ci95'][1]:.3f}]", flush=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    with (SAIDA / "h1_corrigido.csv").open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    # Segunda parte da H1: inclinação de D em log10(λ), por N, com intervalo pivotal.
    tendencias = []
    for n in TAMANHOS:
        if not all((n, mu) in sorteios for mu in LAMBDAS):
            continue
        x = np.log10(LAMBDAS)
        x = x - x.mean()
        pontos = np.array([sorteios[(n, mu)][0] for mu in LAMBDAS])
        referencia = np.array([sorteios[(n, mu)][1] for mu in LAMBDAS])
        replicas = np.array([sorteios[(n, mu)][2] for mu in LAMBDAS])
        tamanho = min(len(r) for r in replicas)
        replicas = np.stack([r[:tamanho] for r in replicas])
        inclinacao = float(x @ pontos / (x @ x))
        centro = float(x @ referencia / (x @ x))
        baixo, alto = np.quantile(x @ replicas / (x @ x) - centro, [0.025, 0.975])
        tendencias.append({"n": n, "inclinacao": inclinacao,
                           "ci95_low": inclinacao - alto, "ci95_high": inclinacao - baixo})
        print(f"N={n}: inclinação de D por década de λ = {inclinacao:.3f} "
              f"[{inclinacao - alto:.3f}; {inclinacao - baixo:.3f}]", flush=True)
    with (SAIDA / "h1_tendencia.csv").open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(tendencias[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(tendencias)
    print("Gravado: figuras/dados/h1_corrigido.csv e h1_tendencia.csv")


def _ordens_celula(n: int, mu: float, repeticoes: int = 2000, semente: int = 71001) -> dict:
    """R1 (probabilidades, via m_i = 2P_e − 1), R2 e R3 corrigidos, com réplicas bootstrap.

    Mesma unidade de reamostragem (blocos), mesma semente e mesmo intervalo pivotal de h1.
    """
    from neutrinos.study_analysis import connected, metrics, noise_corrected_error
    caminhos = [arquivo(n, mu, s) for s in (None, *SEMENTES)]
    exato = np.load(caminhos[0])
    blocos = [dict(np.load(c)) for c in caminhos[1:]]
    referencias = (exato["m1"], exato["c2"], exato["c3"])
    momentos = [np.stack([b[k] for b in blocos]) for k in ("m1", "m2", "m3")]
    por_bloco = [connected(b["m1"], b["m2"], b["m3"], n) for b in blocos]
    valores_bloco = (momentos[0], np.stack([c for c, _ in por_bloco]), np.stack([c for _, c in por_bloco]))

    def estimativas(indice):
        m = [x[indice].mean(axis=0) for x in momentos]
        c2, c3 = connected(*m, n)
        return (m[0], c2, c3)

    todos = np.arange(len(blocos))
    centrais = estimativas(todos)
    corrigido = [noise_corrected_error(r, e, v)["normalized_rmse"]
                 for r, e, v in zip(referencias, centrais, valores_bloco)]
    bruto = [metrics(r, e)["normalized_rmse"] for r, e in zip(referencias, centrais)]
    rng = np.random.default_rng(semente)
    replicas = []
    for _ in range(repeticoes):
        indice = rng.integers(0, len(blocos), len(blocos))
        e = estimativas(indice)
        replicas.append([noise_corrected_error(r, x, v[indice])["normalized_rmse"]
                         for r, x, v in zip(referencias, e, valores_bloco)])
    return {"n": n, "mu": mu, "corrigido": corrigido, "bruto": bruto,
            "replicas": np.asarray(replicas, dtype=float)}


def ordens(processos: int) -> None:
    """Primeira parte de H1 com P_e (R3 − R1) e segunda parte como inclinação de R3 em log10(λ)."""
    celulas = [(n, mu) for n in TAMANHOS for mu in LAMBDAS]
    with ProcessPoolExecutor(processos) as executor:
        resultados = {(r["n"], r["mu"]): r for r in executor.map(_ordens_celula, *zip(*celulas))}

    def pivotal(ponto, referencia, sorteios):
        baixo, alto = np.nanquantile(np.asarray(sorteios) - referencia, [0.025, 0.975])
        return ponto - alto, ponto - baixo

    linhas = []
    for (n, mu), r in sorted(resultados.items()):
        r1, r2, r3 = r["corrigido"]
        b1, _, b3 = r["bruto"]
        lo, hi = pivotal(r3 - r1, b3 - b1, r["replicas"][:, 2] - r["replicas"][:, 0])
        linhas.append({"n": n, "mu": mu, "r1": r1, "r2": r2, "r3": r3,
                       "r3_menos_r1": r3 - r1, "ci95_low": lo, "ci95_high": hi})
        print(f"N={n} λ={mu:g}: R1={r1:.3f} R2={r2:.3f} R3={r3:.3f} | R3−R1={r3 - r1:.3f} [{lo:.3f}; {hi:.3f}]",
              flush=True)
    with (SAIDA / "h1_ordens.csv").open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    x = np.log10(LAMBDAS)
    x = x - x.mean()
    tendencias = []
    for n in TAMANHOS:
        pontos = np.array([resultados[(n, mu)]["corrigido"][2] for mu in LAMBDAS])
        brutos = np.array([resultados[(n, mu)]["bruto"][2] for mu in LAMBDAS])
        sorteios = np.stack([resultados[(n, mu)]["replicas"][:, 2] for mu in LAMBDAS])
        inclinacao = float(x @ pontos / (x @ x))
        lo, hi = pivotal(inclinacao, float(x @ brutos / (x @ x)), x @ sorteios / (x @ x))
        tendencias.append({"n": n, "inclinacao_r3": inclinacao, "ci95_low": lo, "ci95_high": hi})
        print(f"N={n}: inclinação de R3 por década de λ = {inclinacao:.3f} [{lo:.3f}; {hi:.3f}]", flush=True)
    with (SAIDA / "h1_tendencia_r3.csv").open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(tendencias[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(tendencias)
    print("Gravado: figuras/dados/h1_ordens.csv e h1_tendencia_r3.csv")


def coletivo() -> None:
    """Erro da PSA na correlação coletiva C_ZZ (soma das covariâncias de todos os pares),
    a grandeza usada por Lacroix et al. (2024), comparado ao erro par a par (R2)."""
    from neutrinos.study_analysis import connected, noise_corrected_error, pooled
    linhas = []
    for n in TAMANHOS:
        for mu in LAMBDAS:
            exato = np.load(arquivo(n, mu, None))
            blocos = [dict(np.load(arquivo(n, mu, s))) for s in SEMENTES]
            c2, _ = pooled(blocos, n)
            pares = np.stack([connected(b["m1"], b["m2"], b["m3"], n)[0] for b in blocos])
            soma = noise_corrected_error(exato["c2"].sum(axis=-1)[:, None], c2.sum(axis=-1)[:, None],
                                         pares.sum(axis=-1)[..., None])
            par = noise_corrected_error(exato["c2"], c2, pares)
            linhas.append({"n": n, "mu": mu, "r_coletivo": soma["normalized_rmse"],
                           "r2_pares": par["normalized_rmse"],
                           "ruido_dominante": soma["noise_dominated"] or par["noise_dominated"]})
            print(f"N={n} λ={mu:g}: R(C_ZZ)={soma['normalized_rmse']:.3f} R2={par['normalized_rmse']:.3f}",
                  flush=True)
    with (SAIDA / "h1_coletivo.csv").open("w", newline="", encoding="utf-8") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print("Gravado: figuras/dados/h1_coletivo.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("acao", choices=("gerar", "analisar", "ordens", "coletivo"))
    parser.add_argument("--processos", type=int, default=8)
    args = parser.parse_args()
    if args.acao == "gerar":
        gerar(args.processos)
    elif args.acao == "analisar":
        analisar()
    elif args.acao == "coletivo":
        coletivo()
    else:
        ordens(args.processos)
    sys.exit(0)
