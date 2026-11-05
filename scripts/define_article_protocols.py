#!/usr/bin/env python3
"""Materializa o desenho v1 do artigo; não executa cálculos nem acessa a IBM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "configs/protocols/artigo_v1"
MUS = (.1, .3, 1., 3., 10.)
SIZES = (4, 6, 8)
SHOTS = (1024, 4096, 16384)
TIMES = (1., 2., 4.)
PROFILES = {
    "ideal": {"single_qubit_error": 0., "two_qubit_error": 0., "readout_error": 0.},
    "leve": {"single_qubit_error": .0001, "two_qubit_error": .001, "readout_error": .01},
    "moderado": {"single_qubit_error": .001, "two_qubit_error": .01, "readout_error": .03},
}


def config(n, mu, seed, *, end=10., points=201):
    return {"n": n, "mu": mu, "theta": .2, "t_max": end, "points": points,
            "seed": seed, "flavors": [0] * (n // 2) + [1] * (n - n // 2),
            "omega_values": [.7 + .6 * i / (n - 1) for i in range(n)],
            "g_values": [[float(i != j) for j in range(n)] for i in range(n)]}


def reference(name, n, mu, seed, *, trajectories=4096, substeps=12, end=10., points=201):
    return {"id": name, "action": "classical", "request": {
        "config": config(n, mu, seed, end=end, points=points),
        "trajectories": trajectories, "substeps": substeps}}


def quantum(name, parent, *, steps=16, shots=128):
    return {"id": name, "action": "quantum", "run_from": parent,
            "request": {"steps": steps, "shots": shots, "readout_error": 0.}}


def design_files():
    files = {}
    catalog = {
        "schema_version": 1, "study_id": "correlacoes-tres-neutrinos-v1",
        "status": "desenho-definido-para-revisao",
        "collection_status": "aguarda-reproducao-publicada-e-controles",
        "primary_observable": {"kind": "c3", "definition": "cumulante conectado Kzzz de índices distintos",
                               "reference": "evolucao-exata", "methods": ["psa", "circuito"]},
        "secondary_observables": ["pe", "c2"],
        "common_model": {"sizes": list(SIZES), "mu": list(MUS), "theta": .2,
            "omega_rule": "linspace(0.7, 1.3, N)", "g_rule": "1 fora da diagonal; 0 na diagonal",
            "initial_state": "primeira metade nu_e; segunda metade nu_x",
            "main_time_grid": {"start": 0., "end": 10., "points": 201}},
        "analysis": {
            "primary_outputs": ["Kzzz por trio e tempo", "RMSE contra exato", "maior erro absoluto",
                                "amplitude RMS exata", "erro normalizado quando sinal resolvido"],
            "confidence": .95, "bootstrap_repetitions": 2000,
            "bootstrap_unit": "trajetoria ou bitstring completo; incluir calibração na mitigação",
            "normalized_signal_floor": .0001,
            "integration_max_absolute_difference": {"pe": 1e-6, "c2": 1e-5, "c3": 1e-5},
            "exact_crosscheck_max_absolute_difference": 1e-10,
            "trotter_c3_max_absolute_error": .001,
            "h2_equivalence_margin_c3": .01,
            "threshold_rationale": "Metas operacionais v1 em unidades de Pauli; erro Trotter no máximo 10% da margem H2. Não são limiares universais da literatura.",
            "h1_analysis": "Comparar R3-R2 por configuração e tendência com mu para cada N; apresentar incertezas e casos sem normalização. Não agregar cumulantes com sinais opostos antes do erro.",
            "h2_primary_endpoint": {"n": 4, "mu": 3., "trio": [0, 1, 2], "tau": 2.,
                "noise_profile": "moderado", "shots_per_repetition_total": 16384,
                "repetitions": 20, "total_shots_per_method": 327680},
            "h2_primary_selection": "Caso intermediário fixado no desenho; não escolhido por maximização do sinal observado.",
            "h2_success": "IC95 de circuito-PSA exclui zero E IC95 de circuito-exato inteiramente em [-0.01,0.01], com incerteza PSA e erro residual controlados.",
            "h2_interpretation": {"sem_mitigacao_resolve": "H2 refutada nessa condição",
                "apenas_mitigado_resolve": "apoio a H2 nessa condição",
                "nenhum_resolve": "inconclusivo quanto à necessidade de mitigação"},
            "secondary_endpoints": "Demais condições e trios são análises de sensibilidade; sem promovê-los a teste principal após observar dados. Usar Holm se fizer declarações de detecção múltipla.",
            "pooling": "Agregar momentos/contagens antes de calcular cumulantes; declarar orçamento total das 20 repetições; preservar blocos para estimar incerteza e viés.",
            "implementation_status": "analise-conjunta-e-decisao-estatistica-a-implementar",
            "qiskit_validation": {"status": "primeiro-intervalo-disponivel-demais-instantes-a-implementar",
                "required_cases": {"n": list(SIZES), "mu": list(MUS), "tau": list(TIMES)},
                "requirement": "Comparar o circuito Qiskit com o emulador nos mesmos passos totais e estados; conferir também a referência exata. Não substituir o erro Trotter por uma diferença entre duas implementações do mesmo Trotter."},
        },
        "protocols": [],
    }

    def add(identifier, filename, question, steps, prerequisites, note=""):
        path = f"{BASE}/{filename}.json"
        spec = {"schema_version": 1, "name": identifier,
                "description": question + " Desenho v1; executar somente após os controles especificados no catálogo. " + note,
                "steps": steps}
        files[path] = spec
        counts = {action: sum(step["action"] == action for step in steps)
                  for action in sorted({step["action"] for step in steps})}
        catalog["protocols"].append({"id": identifier, "question": question, "file": path,
            "definition_status": "definido", "execution_status": "compativel-com-runner-atual",
            "analysis_status": "usar-criterios-do-catalogo-analise-a-implementar",
            "prerequisites": prerequisites, "steps": len(steps), "actions": counts, "note": note})

    # Controles físicos: a PSA tem incerteza; seus cumulantes não são exigidos
    # exatamente nulos em todas as combinações de tempos e trios.
    steps = []
    for n in SIZES:
        parent = f"controle_n{n}"
        steps.extend([reference(parent, n, 0., 1000 + n), quantum(f"ideal_n{n}", parent),
                      {"id": f"qiskit_n{n}", "action": "circuit", "run_from": parent, "request": {"steps": 16}}])
    add("T01-controles", "01_controles", "Conferir caso sem interação e consistência Qiskit.",
        steps, ["testes-de-software"], "Checar exato/MF e Kzzz exato nulo; avaliar PSA com sua incerteza.")

    for mode in ("integracao", "amostragem"):
        steps = []
        for n in (4, 8):
            for m, mu in enumerate((.1, 1., 10.)):
                for seed in range(1, 6):
                    settings = (2, 4, 8, 12) if mode == "integracao" else (512, 1024, 2048, 4096)
                    for value in settings:
                        steps.append(reference(f"n{n}_m{m}_s{seed}_{value}", n, mu, seed,
                            trajectories=4096 if mode == "integracao" else value,
                            substeps=value if mode == "integracao" else 12))
        add(f"T02-{mode}", f"02_{mode}", f"Quantificar convergência de {mode} da PSA nos trios.",
            steps, ["T01-controles", "reproducao-publicada"])

    for name, sizes in (("principal", SIZES), ("extensao", (12, 16))):
        steps = [reference(f"n{n}_m{m}_s{seed}", n, mu, seed)
                 for n in sizes for m, mu in enumerate(MUS) for seed in range(10001, 10021)]
        add(f"T03-classica-{name}", f"03_classica_{name}",
            "Medir a precisão de Kzzz da PSA contra o exato, por N e interação.", steps,
            ["T02-integracao", "T02-amostragem"] + (["medicao-de-memoria-tempo-e-disco"] if name == "extensao" else []),
            "O runner atual recalcula a referência em cada semente; otimizar o reaproveitamento antes da coleta extensa.")

    steps = []
    for n in SIZES:
        for m, mu in enumerate(MUS):
            parent = f"n{n}_m{m}"
            steps.append(reference(parent, n, mu, 2000 + n * 10 + m, trajectories=256))
            steps.extend(quantum(f"{parent}_t{value}", parent, steps=value) for value in (1, 2, 4, 8, 16))
    add("T04-trotter", "04_trotter", "Quantificar erro ideal de Trotter em Kzzz.", steps,
        ["T01-controles", "reproducao-publicada"], "Analisar ideal_c3; shots=128 são saída auxiliar do emulador local. A referência é o exato. A checagem Qiskit em instantes posteriores ainda precisa ser implementada conforme o catálogo.")

    steps = []
    for n in SIZES:
        for m, mu in enumerate(MUS):
            for seed in range(20001, 20021):
                parent = f"n{n}_m{m}_s{seed}"
                steps.append(reference(parent, n, mu, seed))
                steps.extend(quantum(f"{parent}_shots{shots}", parent, shots=shots) for shots in SHOTS)
    add("T05-medicoes", "05_medicoes", "Medir o efeito de shots na reconstrução dos cumulantes de três corpos.",
        steps, ["T02-integracao", "T02-amostragem", "T04-trotter"],
        "20 repetições por orçamento; o total agregado é 20 vezes shots. Sem ruído de portas ou leitura.")

    steps = []
    for m, mu in enumerate(MUS):
        for t, end in enumerate(TIMES):
            for seed in range(30001, 30021):
                parent = f"m{m}_t{t}_s{seed}"
                # Sete intervalos * 16 subpassos = 112, abaixo do teto Aer (120).
                steps.extend([reference(parent, 4, mu, seed, end=end, points=8),
                              quantum(f"{parent}_ideal", parent)])
                for profile, rates in PROFILES.items():
                    for shots in SHOTS:
                        steps.append({"id": f"{parent}_{profile}_{shots}", "action": "aer",
                            "run_from": parent, "request": {"interval_index": 7, "steps": 16,
                                "shots": shots, "kind": "c3", "index": 0, **rates}})
    add("T06-ruido", "06_ruido", "Quantificar viés e incerteza de K012 em circuitos com ruído de portas e leitura.",
        steps, ["T02-integracao", "T02-amostragem", "T04-trotter", "validacao-ideal-da-grade-de-ruido"],
        "N=4, tau=1/2/4, trio012. Grade própria de 8 pontos até cada tau; 112 subpassos totais no ponto final. Validar essa discretização contra exato antes de interpretar o ruído.")

    specs = {
        "reproducao_publicada": {
            "id": "T00-reproducao-publicada", "definition_status": "alvo-definido",
            "execution_status": "aguarda-conversao-e-validacao-do-Hamiltoniano",
            "source": "https://arxiv.org/html/2409.20215v2", "target": "Figura 2(c), secao III.1.1, N=8, PSA bi-valuada",
            "required_before_execution": ["conversao documentada de unidades, bases, spins/Pauli e soma de pares",
                "parametros e janela extraidos da figura", "dados da fonte ou digitalizacao com incerteza",
                "suporte a 10000 trajetorias em blocos"],
            "acceptance": "Comparar separadamente exato e PSA com suas curvas publicadas; tolerância baseada na precisão da fonte e de amostragem.",
        },
        "mitigacao": {
            "id": "T07-mitigacao", "definition_status": "definido", "execution_status": "aguarda-implementacao",
            "primary_endpoint": catalog["analysis"]["h2_primary_endpoint"],
            "sensitivity_grid": {"n": 4, "mu": list(MUS), "tau": list(TIMES), "trio": [0, 1, 2],
                "profiles": ["leve", "moderado"], "shots_per_repetition_total": list(SHOTS)},
            "seeds": list(range(40001, 40021)), "profiles": PROFILES,
            "method": "Mitigação tensorial de leitura com matrizes 2x2 por qubit; hipótese de erros independentes.",
            "calibration_states": ["0000", "1111"],
            "budget": {"unmitigated_signal_fraction": 1., "mitigated_signal_fraction": .75,
                       "calibration_shots_fraction_each_state": .125,
                       "rule": "Orçamento total idêntico por método, incluindo calibração; declarar também total das 20 repetições."},
            "matrix_condition_number_max": 10.,
            "unstable_calibration_policy": "Registrar como não resolvido; não inverter matriz instável nem excluir o caso silenciosamente.",
            "uncertainty": "Bootstrap conjunto de contagens de sinal, calibração e trajetórias PSA; registrar viés de amostragem.",
            "decision": catalog["analysis"]["h2_success"],
        },
        "hardware_ibm": {
            "id": "T08-hardware", "definition_status": "procedimento-definido",
            "execution_status": "condicionado-a-T07-profundidade-calibracao-e-orcamento",
            "candidate_endpoint": {"n": 4, "mu": 3., "trio": [0, 1, 2], "tau": 2.},
            "device": "Selecionar dispositivo disponível e registrar o nome antes da coleta; não fixar disponibilidade futura.",
            "prerequisites": ["T07-mitigacao", "residual ideal K3 <= 0.001 no circuito a enviar",
                "profundidade e portas após transpilar registradas", "orçamento total autorizado e janela de calibração definida"],
            "policy": "Nenhum envio automático durante definição. Se o teto interativo de 16 subpassos não alcançar a precisão, ajustar a implementação e versionar o protocolo antes de submeter.",
            "archive": ["QPY", "layout", "calibracao", "Runtime options", "job ID", "contagens", "data e horario"],
        },
    }
    for name, spec in specs.items():
        path = f"{BASE}/especificacoes/{name}.json"
        files[path] = spec
        catalog["protocols"].append({"id": spec["id"], "file": path,
            "definition_status": spec["definition_status"], "execution_status": spec["execution_status"],
            "format": "especificacao-cientifica-nao-executavel-pelo-runner"})
    catalog["noise_profiles"] = PROFILES
    catalog["amendments"] = "Se um controle falhar, preservar o resultado e registrar uma versão nova com motivo e alterações antes de nova coleta; não alterar silenciosamente a grade ou os critérios."
    files["configs/estudos/artigo_v1.json"] = catalog
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Conferir se os JSONs correspondem ao desenho, sem gravar")
    args = parser.parse_args()
    differences = []
    for name, value in design_files().items():
        path = ROOT / name
        text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                differences.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            if "steps" in value:
                print(f"{name}: {len(value['steps'])} etapas")
    if differences:
        raise SystemExit("Definições divergentes: " + ", ".join(differences))
    print("Desenho v1 conferido" if args.check else "Desenho v1 salvo; nenhum experimento foi executado")


if __name__ == "__main__":
    main()
