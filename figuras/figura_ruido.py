"""Figura da H2: estimativa de C3 no caso principal sob ruído de leitura e de porta.

Lê figuras/dados/varredura_ruido.csv (scripts/varredura_ruido.py) e grava
figuras/figura-varredura-ruido.pdf.

(a) sem ruído de porta, em função do erro de leitura ε;
(b) com ε = 0,03, em função da despolarização de dois qubits p.
Barras: IC95 da diferença circuito − exato, somado ao exato e ampliado pelo resíduo.

Uso: python figuras/figura_ruido.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import estilo

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "figuras" / "dados" / "varredura_ruido.csv"
SAIDA = RAIZ / "figuras" / "figura-varredura-ruido.pdf"
COR = {"raw": "#3a3a3a", "mitigated": "#c4501b"}
NOME = {"raw": "Bruto", "mitigated": "Mitigado"}
DESLOCAMENTO = {"raw": -0.12, "mitigated": 0.12}
LEITURA_FIXA = 0.03


def main() -> None:
    estilo.aplicar()
    linhas = list(csv.DictReader(DADOS.open(encoding="utf-8")))
    for r in linhas:
        for k in ("erro_porta", "erro_leitura", "estimativa", "exato", "psa", "dif_exato_low", "dif_exato_high"):
            r[k] = float(r[k])
    exato, psa = linhas[0]["exato"], linhas[0]["psa"]

    fig, eixos = plt.subplots(1, 2, sharey=True,
                              figsize=(estilo.LARGURA_TEXTO_CM * estilo.CM, 6.0 * estilo.CM))
    paineis = (
        ("(a)", lambda r: r["erro_porta"] == 0, "erro_leitura", "Erro de leitura, $\\varepsilon$",
         lambda v: estilo.numero(v)),
        ("(b)", lambda r: r["erro_leitura"] == LEITURA_FIXA, "erro_porta",
         "Despolarização de dois qubits, $p$", lambda v: "0" if v == 0 else estilo.potencia(v)),
    )
    for eixo, (letra, filtro, chave, rotulo, formato) in zip(eixos, paineis):
        selecao = [r for r in linhas if filtro(r)]
        valores = sorted({r[chave] for r in selecao})
        posicao = {v: i for i, v in enumerate(valores)}
        eixo.axhline(exato, color="black", linewidth=0.8)
        for limite in (exato - 0.01, exato + 0.01):
            eixo.axhline(limite, color="black", linewidth=0.5, linestyle=(0, (1, 1.5)))
        eixo.axhline(psa, color="0.45", linewidth=0.8, linestyle=(0, (4, 2)))
        for metodo in ("raw", "mitigated"):
            pontos = sorted((r for r in selecao if r["metodo"] == metodo), key=lambda r: r[chave])
            x = np.array([posicao[r[chave]] for r in pontos]) + DESLOCAMENTO[metodo]
            y = np.array([r["estimativa"] for r in pontos])
            baixo = np.array([exato + r["dif_exato_low"] for r in pontos])
            alto = np.array([exato + r["dif_exato_high"] for r in pontos])
            eixo.errorbar(x, y, yerr=[np.clip(y - baixo, 0, None), np.clip(alto - y, 0, None)],
                          color=COR[metodo], marker="o", markersize=3.2, linestyle="none",
                          elinewidth=0.8, capsize=0, label=NOME[metodo])
        eixo.set_xticks(range(len(valores)), [formato(v) for v in valores])
        eixo.set_xlim(-0.6, len(valores) - 0.4)
        eixo.set_xlabel(rotulo)
        eixo.text(0.02, 0.98, letra, transform=eixo.transAxes, ha="left", va="top")

    direita = eixos[1]
    direita.text(len(sorted({r["erro_porta"] for r in linhas})) - 0.3, exato, "exato",
                 ha="left", va="center", fontsize=8)
    direita.text(len(sorted({r["erro_porta"] for r in linhas})) - 0.3, psa, "PSA",
                 ha="left", va="center", fontsize=8, color="0.35")
    eixos[0].set_ylabel(r"$C^{(3)}_{012}$ em $\tau=2$")
    eixos[0].yaxis.set_major_formatter(estilo.formatador_decimal)
    eixos[0].set_ylim(min(exato - 0.05, min(r["estimativa"] for r in linhas) - 0.01), psa + 0.03)
    eixos[0].legend(loc="center left", bbox_to_anchor=(0.0, 0.62), frameon=False, handletextpad=0.3)
    fig.subplots_adjust(wspace=0.08)
    fig.savefig(SAIDA)
    fig.savefig(SAIDA.with_suffix(".svg"))  # vetorial, exibido no Markdown
    fig.savefig(SAIDA.with_suffix(".png"), dpi=300)  # pré-visualização
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
