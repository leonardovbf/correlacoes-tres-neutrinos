"""Estilo único das figuras do artigo (formato SBC).

- Fonte com serifa no padrão Times, como o template SBC, inclusive na matemática.
- Vírgula decimal e ponto de milhar, como no texto em português.
- Uma cor fixa por intensidade de interação λ, em rampa de um único tom
  (λ é ordenado); a identidade também vem de rótulos diretos, não só da cor.
- Exportação vetorial (PDF) na largura final da coluna.
"""
from __future__ import annotations

import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

LARGURA_TEXTO_CM = 16.0  # largura útil da página A4 no template SBC
CM = 1 / 2.54

LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0)
COR_LAMBDA = {0.1: "#4f9bcf", 0.3: "#2f7ebc", 1.0: "#1662a8", 3.0: "#08468b", 10.0: "#08306b"}


def aplicar() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "STIXGeneral"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.grid": False,
        "lines.linewidth": 1.0,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,  # fontes embutidas como TrueType, texto selecionável
    })


def numero(valor: float, casas: int | None = None) -> str:
    """Formata no padrão brasileiro: 1.024 e 0,5."""
    if casas is None:
        texto = f"{valor:,.10g}" if abs(valor) >= 1000 else f"{valor:.10g}"
    else:
        texto = f"{valor:,.{casas}f}"
    texto = texto.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return texto.replace("-", "\u2212")  # sinal de menos tipográfico


def potencia(valor: float) -> str:
    """Rótulo de eixo logarítmico: 2×10⁻⁴ em notação matemática, mantissa com vírgula."""
    from math import floor, log10
    expoente = floor(log10(valor))
    mantissa = round(valor / 10**expoente, 6)
    base = rf"10^{{{expoente}}}"
    if mantissa == 1:
        return rf"${base}$"
    return rf"${numero(mantissa).replace(',', '{,}')}\times{base}$"


formatador_decimal = FuncFormatter(lambda v, _: numero(v))
formatador_potencia = FuncFormatter(lambda v, _: potencia(v) if v > 0 else "")


def rotulo_lambda(mu: float) -> str:
    return rf"$\lambda={numero(mu).replace(',', '{,}')}$"
