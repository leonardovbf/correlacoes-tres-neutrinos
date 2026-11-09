"""Tabelas do artigo em Markdown, geradas a partir do pacote de resultados.

- tabela_controles.md: Tabela 4 completa (limite e máximo observado por controle).
- tabela_circuitos.md: passos de Trotter, profundidade e CNOTs dos circuitos ruidosos,
  com o menor número de passos que respeita a tolerância de Trotter (|ΔC3| ≤ 10⁻³).
- tabela_d.md: D = R3 − R2 por configuração, com IC95 (substitui a Fig. 3).
  Se figuras/dados/h1_corrigido.csv existir, usa os valores corrigidos do ruído.

Uso: PYTHONPATH=src python figuras/gerar_tabelas.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

from estilo import numero

RAIZ = Path(__file__).resolve().parents[1]
PACOTE = next((RAIZ / "analysis" / "article_packages").glob("*/"))
SAIDA = RAIZ / "figuras" / "tabelas"


def relatorio(nome: str) -> dict:
    return json.loads((PACOTE / "reports" / f"{nome}.json").read_text(encoding="utf-8"))


def maximo(nome: str, padrao: str) -> tuple[float, float]:
    checks = [c for c in relatorio(nome)["checks"] if re.search(padrao, c["name"])]
    if not checks or not all(c["pass"] for c in checks):
        raise ValueError(f"{nome}: controle ausente ou reprovado ({padrao})")
    return max(c["value"] for c in checks), checks[0]["limit"]


def cientifico(valor: float) -> str:
    if valor == 0:
        return "$0$"
    expoente = int(np.floor(np.log10(abs(valor))))
    mantissa = valor / 10**expoente
    if round(mantissa, 2) == 1:
        return f"$10^{{{expoente}}}$"
    return f"${numero(mantissa, 2)}\\times10^{{{expoente}}}$"


def tabela(cabecalho: list[str], alinhamento: list[str], linhas: list[list[str]]) -> str:
    regua = {"e": ":---", "d": "---:", "c": ":---:"}
    partes = ["| " + " | ".join(cabecalho) + " |",
              "| " + " | ".join(regua[a] for a in alinhamento) + " |"]
    partes += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return "\n".join(partes) + "\n"


def controles() -> str:
    from neutrinos.study_analysis import independent_exact_check
    exato = independent_exact_check()
    itens = [
        ("Reprodução publicada: exato", *maximo("T00-reproducao-publicada", r"exact ν")),
        ("Reprodução publicada: PSA", *maximo("T00-reproducao-publicada", r"psa ν")),
        ("Exato: hamiltoniano denso independente", max(exato.values()), 1e-10),
        ("Sem interação: $C^{(3)}$ exato", *maximo("T01-controles", r"K3 sem intera")),
        ("Qiskit versus emulador", *maximo("T04-qiskit", r"^qiskit_n\d+_m\d+_tau\d+$")),
        ("Refinamento RK4: $P_e$", *maximo("T02-integracao", r" psa pe$")),
        ("Refinamento RK4: cumulantes", *maximo("T02-integracao", r" psa c[23]$")),
        ("Erro-padrão da PSA: $C^{(3)}$", *maximo("T02-amostragem-suplementar", r"erro padrão PSA")),
        ("Trotter ideal: $C^{(3)}$", *maximo("T04-trotter", r"^n\d+_m\d+_t\d+$")),
    ]
    linhas = [[nome, cientifico(limite), cientifico(valor)] for nome, valor, limite in itens]
    return tabela(["Controle", "Limite", "Máximo observado"], ["e", "d", "d"], linhas)


def circuitos() -> str:
    from qiskit import transpile
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler import CouplingMap
    from neutrinos.qiskit_backend import build_trotter_circuit
    from neutrinos.sim import ExperimentConfig, classical_exact

    def c3(probabilidades, trio=(0, 1, 2)):
        indice = np.arange(len(probabilidades))
        z = {q: 1 - 2 * ((indice >> q) & 1) for q in range(4)}
        m = lambda *qs: float(np.sum(probabilidades * np.prod([z[q] for q in qs], axis=0)))
        i, j, k = trio
        return m(i, j, k) - m(i) * m(j, k) - m(j) * m(i, k) - m(k) * m(i, j) + 2 * m(i) * m(j) * m(k)

    def medidas(config, tau, passos):
        circuito = build_trotter_circuit(config, tau, passos)
        linha = transpile(circuito, basis_gates=["rz", "sx", "x", "cx"],
                          coupling_map=CouplingMap.from_line(4), optimization_level=1, seed_transpiler=1)
        return linha.depth(), int(linha.count_ops().get("cx", 0))

    linhas = []
    for mu in (0.1, 0.3, 1.0, 3.0, 10.0):
        for tau in (1.0, 2.0, 4.0):
            pontos = 29 if (mu, tau) == (10.0, 4.0) else 8  # emenda de discretização
            config = ExperimentConfig(n=4, mu=mu, theta=0.2, t_max=tau, points=pontos, seed=30001,
                                      flavors=(0, 0, 1, 1), omega_values=(0.7, 0.9, 1.1, 1.3))
            usados = 16 * (pontos - 1)
            exato = classical_exact(config).c3[-1, 0]
            minimo = next((p for p in range(1, usados + 1)
                           if abs(c3(Statevector.from_instruction(build_trotter_circuit(config, tau, p))
                                     .probabilities()) - exato) <= 1e-3), None)
            profundidade, cx = medidas(config, tau, usados)
            profundidade_min, cx_min = medidas(config, tau, minimo)
            linhas.append([numero(mu), numero(tau), numero(usados), numero(profundidade), numero(cx),
                           numero(minimo), numero(profundidade_min), numero(cx_min)])
            print(f"circuito λ={mu} τ={tau}: {usados} passos/{cx} CX; mínimo {minimo}/{cx_min} CX", flush=True)
    return tabela(["$\\lambda$", "$\\tau$", "Passos", "Profundidade", "CNOTs",
                   "Passos mín.", "Profundidade", "CNOTs"], ["d"] * 8, linhas)


def tabela_d() -> str:
    corrigido = RAIZ / "figuras" / "dados" / "h1_corrigido.csv"
    if corrigido.exists():
        fontes, chaves = [corrigido], ("r3_minus_r2", "ci95_low", "ci95_high")
    else:
        fontes = [PACOTE / "tables" / "h1_main.csv", PACOTE / "tables" / "h1_extension.csv"]
        chaves = ("r3_minus_r2", "delta_ci95_low", "delta_ci95_high")
    linhas = []
    for fonte in fontes:
        for r in csv.DictReader(fonte.open(encoding="utf-8")):
            d, baixo, alto = (float(r[k]) for k in chaves)
            linhas.append([numero(int(r["n"])), numero(float(r["mu"])), numero(d, 3),
                           f"[{numero(baixo, 3)}; {numero(alto, 3)}]"])
    nota = "corrigido do ruído amostral" if corrigido.exists() else "bruto (pacote original)"
    print(f"tabela D: {len(linhas)} configurações, {nota}")
    return tabela(["$N$", "$\\lambda$", "$D$", "IC95"], ["d", "d", "d", "c"], linhas)


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, gerar in (("tabela_controles", controles), ("tabela_d", tabela_d),
                        ("tabela_circuitos", circuitos)):
        (SAIDA / f"{nome}.md").write_text(gerar(), encoding="utf-8")
        print(f"Gravado: figuras/tabelas/{nome}.md", flush=True)


if __name__ == "__main__":
    main()
