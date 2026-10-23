# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Gera os três diagramas originais de ARTIGO.md.

Executar da raiz do repositório: uv run figuras/gerar_diagramas.py
Saídas: SVG com texto editável e PNG a 450 dpi; largura física de 170 mm.
As versões em português ficam em figuras/ e as inglesas em figuras/en/.
Usar --idioma pt ou --idioma en para gerar somente uma versão.
Todos os desenhos são esquemáticos, sem dados de simulações ou escala física.

Fundamentação e exemplos consultados em 23/10/2026:
- Janka (2012): colapso, choque estagnado e aquecimento por neutrinos.
  https://doi.org/10.1146/annurev-nucl-102711-094901
- Riccio e Balantekin, Eqs. (47) e (52): cumulantes e fechamento.
  https://arxiv.org/html/2607.28619v2
- Lacroix et al. (2024), Figs. 2–4: comparação por observável e tamanho.
  https://doi.org/10.1103/PhysRevD.110.103027
- Hall et al. (2021), Figs. 1–3: algoritmo e separação exato/Trotter/medições.
  https://doi.org/10.1103/PhysRevD.104.063009
- Illa e Savage (2023), Fig. 1 e Fig. S3: circuitos e correlações com incertezas.
  https://doi.org/10.1103/PhysRevLett.130.221003

Convenções: painéis identificados, legenda externa, paleta sóbria e informação
redundante em texto e forma. A rede da Figura 3 ilustra apenas a conectividade
do modelo, sem representar a geometria de um processador ou um resultado.
https://journals.aps.org/authors/style-basics
https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/
"""

import argparse
from itertools import combinations
from math import cos, pi, sin
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle


OUT = Path(__file__).resolve().parent
INK = "#23364b"
MUTED = "#627286"
BLUE = "#286da8"
TEAL = "#267e83"
GOLD = "#b77329"
RULE = "#d7dfe7"
PALE_BLUE = "#edf4fa"
PALE_GOLD = "#fcf3e6"
MM = 1 / 25.4
LANGUAGE = "pt"
LABELS_EN = {
    "Colapso": "Collapse", "Choque e neutrinos": "Shock and neutrinos",
    "Desfechos": "Outcomes", "núcleo": "core", "PN": "PNS",
    "Contração e rebote": "Contraction and bounce",
    "Formação do choque": "Shock formation",
    "Aquecimento atrás do choque": "Heating behind the shock",
    "Neutrinos e movimentos da matéria": "Neutrinos and fluid motion",
    "Explosão": "Explosion", "Choque reativado": "Revived shock",
    "Possível buraco negro": "Possible black hole",
    "matéria em queda": "Infalling matter",
    "região de aquecimento": "Heating region", "neutrinos": "Neutrinos",
    "Individuais": "Individual means", "Pares e uma média": "Pairs and a mean",
    "Parcela do trio": "Three-body term", "três médias": "three means",
    "três contribuições de pares": "three pair contributions",
    "cumulante conectado": "connected cumulant",
    "Modelo comum": "Shared model", "Métodos": "Methods", "Comparação": "Comparison",
    "Dois sabores": "Two flavors", "Energias distintas": "Distinct energies",
    "Exato": "Exact", "Referência · N = 4–16": "Reference · N = 4–16",
    "Campo médio": "Mean field",
    "Médias fatorizadas · N = 4–16": "Factorized means · N = 4–16",
    "Trajetórias · N = 4–16": "Trajectories · N = 4–16",
    "Circuitos": "Circuits", "Observáveis comuns": "Shared observables",
    "Desvios do exato": "Deviations from exact",
    "erros e incertezas": "errors and uncertainties", "CONTROLES": "CONTROLS",
    "Integração": "Integration", "tolerâncias": "tolerances",
    "amostragem": "sampling", "passo temporal": "time step",
    "Medições": "Measurements", "incerteza": "uncertainty",
    "Ruído": "Noise", "mitigação": "mitigation",
}
FIGURES_EN = {
    "figura-1-colapso-estelar": (
        "figure-1-core-collapse", "Core collapse and neutrino heating",
        "Panels show a contracting stellar core, a stalled shock surrounding "
        "a proto-neutron star, neutrino heating, and possible outcomes of "
        "explosion or black-hole formation. The diagrams are not to scale."),
    "figura-2-correlacoes-conectadas": (
        "figure-2-connected-correlations", "Decomposition of a three-particle moment",
        "Three groups distinguish individual means, pair cumulants times a "
        "mean, and the connected three-body cumulant. A central three-legged "
        "symbol denotes the cumulant and does not represent another particle, "
        "an additional Hamiltonian interaction, or an entanglement witness."),
    "figura-3-protocolo-comparacao": (
        "figure-3-comparison-protocol", "Proposed comparison protocol",
        "Three columns show the shared model, four evolution methods, and "
        "observables compared with exact evolution. The four-node network "
        "illustrates all-to-all model interactions. The bottom row lists "
        "integration, sampling, Trotter, measurement, and noise controls."),
}
plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9,
    "text.color": INK,
    "svg.fonttype": "none",
    "svg.hashsalt": "neutrinos-diagramas-v2",
    "mathtext.fontset": "dejavusans",
    "savefig.facecolor": "white",
    "axes.unicode_minus": False,
})


def canvas(height):
    fig = plt.figure(figsize=(170 * MM, height * MM))
    ax = fig.add_axes((0, 0, 1, 1), xlim=(0, 170), ylim=(0, height))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def label(ax, x, y, value, size=9, weight="normal", color=INK, ha="center", **kw):
    if LANGUAGE == "en":
        value = LABELS_EN.get(value, value).replace("0{,}1", "0.1")
    return ax.text(x, y, value, ha=ha, va="center", fontsize=size, color=color,
                   fontweight=weight, linespacing=1.25, **kw)


def line(ax, xs, ys, color=RULE, width=0.7, **kw):
    ax.plot(xs, ys, color=color, linewidth=width, solid_capstyle="round", **kw)


def arrow(ax, start, end, color=INK, width=0.9, size=8, **kw):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=size,
                                linewidth=width, color=color, shrinkA=0,
                                shrinkB=0, **kw))


def polar(cx, cy, r, angle):
    return cx + r * cos(angle), cy + r * sin(angle)


def radial_arrow(ax, cx, cy, r1, r2, angle, **kw):
    arrow(ax, polar(cx, cy, r1, angle), polar(cx, cy, r2, angle), **kw)


def shock(ax, cx, cy, r, color=INK, amplitude=0.5, fill="none", width=1.1):
    points = [polar(cx, cy, r + amplitude * sin(8 * theta), theta)
              for theta in [2 * pi * i / 240 for i in range(241)]]
    ax.add_patch(Polygon(points, closed=True, facecolor=fill,
                         edgecolor=color, linewidth=width))


def panel(ax, x, y, letter, title, end):
    label(ax, x, y, f"({letter})", size=10, weight="bold", ha="left")
    label(ax, x + 7, y, title, size=10, weight="bold", ha="left")
    line(ax, [x, end], [y - 5, y - 5])


def export(fig, stem, title, description):
    """Verifica cortes de texto e exporta também a descrição acessível."""
    target = OUT
    if LANGUAGE == "en":
        stem, title, description = FIGURES_EN[stem]
        target = OUT / "en"
    target.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    for ax in fig.axes:
        for text in ax.texts:
            box = text.get_window_extent(renderer)
            if (box.x0 < -1 or box.y0 < -1 or box.x1 > bounds.x1 + 1
                    or box.y1 > bounds.y1 + 1):
                raise ValueError(f"Texto fora da figura {stem}: {text.get_text()}")
    svg = target / f"{stem}.svg"
    fig.savefig(svg, metadata={"Date": None, "Title": title,
                              "Description": description})
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(svg)
    root = tree.getroot()
    root.set("role", "img")
    root.set("aria-labelledby", "titulo descricao")
    for index, (tag, element_id, value) in enumerate([
        ("title", "titulo", title), ("desc", "descricao", description)
    ]):
        node = ET.Element(f"{{{ns}}}{tag}", {"id": element_id})
        node.text = value
        root.insert(index, node)
    tree.write(svg, encoding="utf-8", xml_declaration=True)
    # Evita espaços em linhas vazias dos SVGs versionados.
    lines = svg.read_text(encoding="utf-8").splitlines()
    svg.write_text("\n".join(line if line.strip() else "" for line in lines) + "\n",
                   encoding="utf-8")
    fig.savefig(target / f"{stem}.png", dpi=450)
    plt.close(fig)
    print(f"Gerados ({LANGUAGE}): {stem}.svg e {stem}.png")


def collapse():
    fig, ax = canvas(96)
    panel(ax, 5, 89, "a", "Colapso", 52)
    panel(ax, 61, 89, "b", "Choque e neutrinos", 112)
    panel(ax, 121, 89, "c", "Desfechos", 165)

    # Corte do núcleo em contração; raios e distâncias não estão em escala.
    cx, cy = 27, 53
    for r, fill, edge in [(20, "#f3f5f8", RULE), (15, "#e2eaf2", "#aebfce"),
                          (10, "#c1d3e4", "#92acc4"), (6, INK, INK)]:
        ax.add_patch(Circle((cx, cy), r, facecolor=fill, edgecolor=edge,
                            linewidth=0.7))
    label(ax, cx, cy, "núcleo", size=8, color="white")
    for angle in (pi / 4, 3 * pi / 4, 5 * pi / 4, 7 * pi / 4):
        radial_arrow(ax, cx, cy, 27, 21, angle, color=MUTED, width=1, size=8)
    label(ax, 27, 22, "Contração e rebote", size=9.5)
    label(ax, 27, 16, "Formação do choque", color=MUTED, size=8.5)
    arrow(ax, (51, 53), (60, 53), width=1, size=9)

    # Aquecimento situado fora da protoestrela de nêutrons e dentro do choque.
    cx, cy = 86, 53
    shock(ax, cx, cy, 20, fill=PALE_GOLD, amplitude=0.55)
    ax.add_patch(Circle((cx, cy), 10, facecolor="white", edgecolor="none"))
    ax.add_patch(Circle((cx, cy), 8.8, facecolor=PALE_BLUE, edgecolor="none"))
    ax.add_patch(Circle((cx, cy), 5.8, facecolor=INK, edgecolor=INK))
    label(ax, cx, cy, "PN", size=8.5, weight="bold", color="white")
    for angle in (pi / 6, 5 * pi / 6, 7 * pi / 6, 11 * pi / 6):
        radial_arrow(ax, cx, cy, 9.4, 17, angle, color=GOLD, width=1, size=8)
    label(ax, 86, 66, r"$\nu$", color=GOLD, size=11)
    for angle in (pi / 4, 3 * pi / 4):
        radial_arrow(ax, cx, cy, 27, 21.5, angle, color=MUTED, width=1, size=8)
    label(ax, 86, 22, "Aquecimento atrás do choque", size=9.5)
    label(ax, 86, 16, "Neutrinos e movimentos da matéria", size=8.5, color=MUTED)

    # As ramificações indicam possibilidades, não um destino fixado pelo sabor.
    line(ax, [107, 116, 116, 124], [53, 53, 68, 68], color=INK, width=0.9)
    line(ax, [116, 116, 131], [53, 29, 29], color=INK, width=0.9)
    arrow(ax, (122, 68), (126, 68), size=7)
    arrow(ax, (129, 29), (133, 29), size=7)
    cx, cy = 144, 68
    shock(ax, cx, cy, 9, color=GOLD, amplitude=0.8, fill=PALE_GOLD)
    ax.add_patch(Circle((cx, cy), 2.8, facecolor=INK, edgecolor="white", linewidth=0.7))
    for angle in (0, pi / 3, 2 * pi / 3, 4 * pi / 3, 5 * pi / 3):
        radial_arrow(ax, cx, cy, 10.5, 15, angle, color=TEAL, width=0.8, size=7)
    label(ax, 144, 47, "Explosão", size=9.5)
    label(ax, 144, 41.5, "Choque reativado", size=8.5, color=MUTED)
    ax.add_patch(Circle((144, 29), 5, facecolor=INK, edgecolor=INK))
    ax.add_patch(Circle((144, 29), 6.5, facecolor="none", edgecolor=MUTED,
                        linewidth=0.65, linestyle=(0, (2, 2))))
    label(ax, 144, 16, "Possível buraco negro", size=9)

    line(ax, [5, 165], [10, 10])
    arrow(ax, (7, 4.5), (14, 4.5), color=MUTED, size=7)
    label(ax, 17, 4.5, "matéria em queda", ha="left", size=8.5, color=MUTED)
    ax.add_patch(Rectangle((61, 3), 6, 3, facecolor=PALE_GOLD, edgecolor=GOLD,
                           linewidth=0.6))
    label(ax, 70, 4.5, "região de aquecimento", ha="left", size=8.5, color=MUTED)
    arrow(ax, (125, 4.5), (132, 4.5), color=GOLD, size=7)
    label(ax, 135, 4.5, "neutrinos", ha="left", size=8.5, color=MUTED)
    export(fig, "figura-1-colapso-estelar", "Colapso e aquecimento por neutrinos",
           "Três painéis mostram o núcleo em contração, o choque estagnado com "
           "uma protoestrela de nêutrons e aquecimento por neutrinos, e os "
           "possíveis desfechos de explosão ou formação de buraco negro. "
           "As regiões e as setas são esquemáticas, sem escala física.")


def trio(ax, cx, cy, scale=1, pair=None, connected=False):
    # Uma ligação de par e um nó de três pernas distinguem C2 e C3.
    points = [(cx, cy + 7 * scale), (cx - 7 * scale, cy - 5 * scale),
              (cx + 7 * scale, cy - 5 * scale)]
    if connected:
        for x, y in points:
            line(ax, [cx, x], [cy - scale, y], color=GOLD, width=1.6, zorder=2)
        ax.add_patch(Polygon([(cx, cy + 0.9 * scale),
                              (cx + 1.9 * scale, cy - scale),
                              (cx, cy - 2.9 * scale),
                              (cx - 1.9 * scale, cy - scale)],
                             facecolor=GOLD, edgecolor=GOLD, zorder=3))
    elif pair:
        a, b = pair
        line(ax, [points[a][0], points[b][0]], [points[a][1], points[b][1]],
             color=BLUE, width=1.5, zorder=2)
    for (x, y), name in zip(points, ("i", "j", "k")):
        ax.add_patch(Circle((x, y), 2.8 * scale, facecolor="white",
                            edgecolor=INK, linewidth=0.85, zorder=4))
        label(ax, x, y, f"${name}$", size=9, zorder=5)


def cumulants():
    fig, ax = canvas(76)
    panel(ax, 6, 69, "a", "Individuais", 39)
    panel(ax, 49, 69, "b", "Pares e uma média", 117)
    panel(ax, 128, 69, "c", "Parcela do trio", 165)
    ax.add_patch(Rectangle((127, 17), 38, 44, facecolor=PALE_GOLD,
                           edgecolor="none", zorder=0))
    label(ax, 23, 57, "três médias", size=8.5, color=MUTED)
    label(ax, 83, 57, "três contribuições de pares", size=8.5, color=MUTED)
    label(ax, 146, 57, "cumulante conectado", size=8.5, color=MUTED)
    trio(ax, 23, 41, scale=1.15)
    label(ax, 23, 22, r"$m_i\,m_j\,m_k$", size=11)
    for cx, pair, equation in [
        (58, (0, 1), r"$C^{(2)}_{ij} m_k$"),
        (84, (0, 2), r"$C^{(2)}_{ik} m_j$"),
        (110, (1, 2), r"$C^{(2)}_{jk} m_i$"),
    ]:
        trio(ax, cx, 41, scale=0.82, pair=pair)
        label(ax, cx, 22, equation, size=10)
    for x in (71, 97):
        label(ax, x, 40, "+", size=12, color=MUTED)
    for x in (43, 122):
        label(ax, x, 40, "+", size=15)
    trio(ax, 146, 41, scale=1.15, connected=True)
    label(ax, 146, 22, r"$C^{(3)}_{ijk}$", size=12)
    line(ax, [6, 165], [14, 14])
    label(ax, 85, 6,
          r"$\langle Z_i Z_j Z_k\rangle = m_i m_j m_k"
          r"+C^{(2)}_{ij}m_k+C^{(2)}_{ik}m_j+C^{(2)}_{jk}m_i+C^{(3)}_{ijk}$", size=10)
    export(fig, "figura-2-correlacoes-conectadas",
           "Decomposição de um momento de três partículas",
           "Três grupos distinguem o produto de médias individuais, os três "
           "termos de cumulante de par vezes média e a parcela conectada do "
           "trio. Uma ligação representa um par e um nó central de três pernas "
           "representa o cumulante de terceira ordem, sem indicar interações "
           "adicionais no Hamiltoniano ou certificar emaranhamento.")


def network(ax, cx, cy):
    points = [polar(cx, cy, 12.5, pi / 2 + i * pi / 2) for i in range(4)]
    for a, b in combinations(range(4), 2):
        line(ax, [points[a][0], points[b][0]], [points[a][1], points[b][1]],
             color="#9eb9d0", width=0.85, zorder=1)
    for i, (x, y) in enumerate(points, 1):
        ax.add_patch(Circle((x, y), 3.1, facecolor=PALE_BLUE, edgecolor=BLUE,
                            linewidth=0.9, zorder=2))
        label(ax, x, y, rf"$\nu_{i}$", size=8.5, zorder=3)


def protocol():
    fig, ax = canvas(110)
    panel(ax, 5, 104, "a", "Modelo comum", 40)
    panel(ax, 51, 104, "b", "Métodos", 114)
    panel(ax, 127, 104, "c", "Comparação", 165)
    label(ax, 24, 91, r"$H,\;|\Psi_0\rangle$", size=12)
    network(ax, 24, 65)
    label(ax, 24, 42, "Dois sabores", size=9.5)
    label(ax, 24, 36, "Energias distintas", size=8.5, color=MUTED)
    label(ax, 24, 29, r"$\mu/\bar{\omega}=0{,}1$–$10$", size=9.5)

    line(ax, [40, 45], [65, 65], color=MUTED, width=0.85)
    line(ax, [45, 45], [33, 84], color=MUTED, width=0.85)
    line(ax, [119, 119], [33, 84], color=MUTED, width=0.85)
    for y, heading, sub, color in [
        (84, "Exato", "Referência · N = 4–16", INK),
        (67, "Campo médio", "Médias fatorizadas · N = 4–16", MUTED),
        (50, "PSA", "Trajetórias · N = 4–16", BLUE),
        (33, "Circuitos", "Qiskit / Trotter · N = 4–8", TEAL),
    ]:
        arrow(ax, (45, y), (50, y), color=MUTED, width=0.8, size=7)
        line(ax, [52, 52], [y - 5, y + 5], color=color, width=2)
        label(ax, 56, y + 3, heading, size=10, weight="bold", ha="left")
        label(ax, 56, y - 3, sub, size=8.5, color=MUTED, ha="left")
        line(ax, [114, 119], [y, y], color=MUTED, width=0.8)
    arrow(ax, (119, 65), (126, 65), color=MUTED, width=0.85, size=8)

    label(ax, 147, 92, "Observáveis comuns", size=8.5, color=MUTED)
    label(ax, 147, 81, r"$P_{e,i}(t)$", size=12)
    label(ax, 147, 67, r"$C^{(2)}_{ij}(t)$", size=12)
    ax.add_patch(Rectangle((129, 46), 36, 13, facecolor=PALE_GOLD, edgecolor="none"))
    label(ax, 147, 52.5, r"$C^{(3)}_{ijk}(t)$", size=12)
    label(ax, 147, 35, "Desvios do exato", size=9.5)
    label(ax, 147, 27, "erros e incertezas", size=8.5, color=MUTED)

    line(ax, [5, 165], [19, 19])
    label(ax, 5, 11.5, "CONTROLES", size=8, weight="bold", color=MUTED, ha="left")
    for x, top, bottom in [
        (53, "Integração", "tolerâncias"), (79, "PSA", "amostragem"),
        (105, "Trotter", "passo temporal"), (131, "Medições", "incerteza"),
        (155, "Ruído", "mitigação"),
    ]:
        label(ax, x, 13, top, size=8.5)
        label(ax, x, 7, bottom, size=8, color=MUTED)
    export(fig, "figura-3-protocolo-comparacao", "Protocolo proposto de comparação",
           "Três colunas mostram o modelo comum, os quatro métodos e os "
           "observáveis comparados à referência exata. A rede de quatro "
           "vértices ilustra interações entre todos os pares, sem especificar "
           "o tamanho final ou a conectividade de hardware. O cumulante do "
           "trio está destacado. A faixa inferior discrimina controles de "
           "integração, amostragem, Trotter, medições e ruído. É um planejamento.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idioma", choices=("pt", "en", "todos"), default="todos")
    args = parser.parse_args()
    for LANGUAGE in (("pt", "en") if args.idioma == "todos" else (args.idioma,)):
        collapse()
        cumulants()
        protocol()
