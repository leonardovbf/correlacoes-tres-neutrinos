"""Figura: RMSE de C3 dos circuitos ideais em função das medições por bloco.

Lê figuras/dados/orcamento_medicoes.csv (gerado por dados_orcamento.py) e grava
figuras/figura-orcamento-medicoes.pdf em formato vetorial.

Uso: python figuras/figura_orcamento.py
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator

import estilo

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "figuras" / "dados" / "orcamento_medicoes.csv"
SAIDA = RAIZ / "figuras" / "figura-orcamento-medicoes.pdf"
ORCAMENTOS = (1024, 4096, 16384)
DESLOCAMENTO = dict(zip(estilo.LAMBDAS, (0.90, 0.95, 1.0, 1.05, 1.10)))  # evita sobreposição


def main() -> None:
    estilo.aplicar()
    series = defaultdict(list)
    for r in csv.DictReader(DADOS.open(encoding="utf-8")):
        series[(int(r["n"]), float(r["mu"]))].append(
            (int(r["medicoes_por_bloco"]), float(r["rmse_c3"]),
             float(r["rmse_c3_p025"]), float(r["rmse_c3_p975"])))
    tamanhos = sorted({n for n, _ in series})

    fig, eixos = plt.subplots(1, len(tamanhos), sharey=True,
                              figsize=(estilo.LARGURA_TEXTO_CM * estilo.CM, 5.6 * estilo.CM))
    for eixo, n in zip(eixos, tamanhos):
        for mu in estilo.LAMBDAS:
            pontos = sorted(series[(n, mu)])
            m = np.array([p[0] for p in pontos]) * DESLOCAMENTO[mu]
            valor = np.array([p[1] for p in pontos])
            baixo = np.array([p[2] for p in pontos])
            alto = np.array([p[3] for p in pontos])
            erro = np.vstack([np.clip(valor - baixo, 0, None), np.clip(alto - valor, 0, None)])
            eixo.errorbar(m, valor, yerr=erro, color=estilo.COR_LAMBDA[mu], marker="o",
                          markersize=3.2, linewidth=0.9, elinewidth=0.7, capsize=0,
                          label=estilo.rotulo_lambda(mu))
        eixo.set_xscale("log", base=2)
        eixo.set_yscale("log")
        eixo.xaxis.set_major_locator(FixedLocator(ORCAMENTOS))
        eixo.xaxis.set_major_formatter(estilo.formatador_decimal)
        eixo.xaxis.set_minor_locator(NullLocator())
        eixo.set_xlim(ORCAMENTOS[0] / 1.6, ORCAMENTOS[-1] * 1.6)
        eixo.set_title(rf"$N={n}$", fontsize=9, pad=4)
        eixo.set_xlabel("Medições por bloco, $m$")

    # Referência de inclinação m^(-1/2), ancorada no primeiro painel.
    referencia = eixos[0]
    base = 4.2e-4
    m = np.array([1024, 4096])
    referencia.plot(m, base * np.sqrt(m[0] / m), color="0.25", linewidth=0.7, linestyle=(0, (3, 2)))
    referencia.text(m[1] * 1.12, base * 0.5, r"$\propto m^{-1/2}$", fontsize=8,
                    ha="left", va="center", color="0.25")

    eixos[0].set_ylabel(r"RMSE de $C^{(3)}$")
    marcas = [2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2]
    eixos[0].yaxis.set_major_locator(FixedLocator(marcas))
    eixos[0].yaxis.set_major_formatter(estilo.formatador_potencia)
    eixos[0].yaxis.set_minor_formatter(NullFormatter())
    eixos[0].set_ylim(1.6e-4, 1.4e-2)

    eixos[-1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False,
                     handlelength=1.6, borderaxespad=0)
    fig.subplots_adjust(wspace=0.12)
    fig.savefig(SAIDA)
    fig.savefig(SAIDA.with_suffix(".svg"))  # vetorial, exibido no Markdown
    fig.savefig(SAIDA.with_suffix(".png"), dpi=300)  # pré-visualização
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
