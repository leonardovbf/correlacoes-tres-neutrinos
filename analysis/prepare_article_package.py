#!/usr/bin/env python3
"""Extrai um pacote de escrita de um estudo concluído e de sua coleta IBM.

Os relatórios originais não são modificados. O pacote resume os casos e guarda
hashes SHA-256 para que cada tabela possa ser conferida nos resultados brutos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

PHASES = (
    "T00-reproducao-publicada", "T01-controles", "T02-integracao",
    "T02-amostragem-suplementar", "T04-trotter", "T04-qiskit",
    "T03-classica-principal", "T03-classica-extensao", "T05-medicoes",
    "T06-ruido", "T07-mitigacao",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def phase_reports(study_path: Path):
    study = read(study_path)
    phases = {item["name"]: item for item in study["phases"]}
    if study["status"] != "completed_local_collection" or set(phases) != set(PHASES):
        raise ValueError("O estudo oficial precisa ter as 11 fases locais concluídas")
    reports = {}
    for name in PHASES:
        phase = phases[name]
        if phase["status"] != "completed" or phase.get("analysis_status") != "passed":
            raise ValueError(f"Fase não validada: {name}")
        for artifact in phase["artifacts"]:
            path = study_path.parent / artifact["path"]
            if digest(path) != artifact["sha256"]:
                raise ValueError(f"Artefato alterado: {path}")
        reports[name] = read(study_path.parent / name / "analysis.json")
    return study, phases, reports


def h1_rows(report: dict) -> list[dict]:
    rows = []
    for item in report["cases"]:
        a = item["psa_analysis"]
        r2, r3 = a["c2"]["normalized_rmse"], a["c3"]["normalized_rmse"]
        ci = a["r3_minus_r2_ci95"]
        rows.append({"n": item["cell"]["n"], "mu": item["cell"]["mu"],
                     "blocks": a["repetitions"], "bootstrap_repetitions": a["bootstrap_repetitions"],
                     "r2": r2, "r3": r3, "r3_minus_r2": None if r2 is None or r3 is None else r3-r2,
                     "delta_ci95_low": None if ci is None else ci[0],
                     "delta_ci95_high": None if ci is None else ci[1],
                     "ci_positive": None if ci is None else ci[0] > 0})
    return rows


def endpoint_rows(report: dict, mitigation: bool) -> list[dict]:
    rows = []
    for item in report["endpoint_cases"]:
        cell, a = item["cell"], item["analysis"]
        row = {"n": cell["n"], "mu": cell["mu"], "tau": cell["tau"],
               "shots_per_block": cell["shots"], "single_qubit_error": cell["single"],
               "two_qubit_error": cell["two"], "readout_error": cell["readout"],
               "blocks": item["repetitions"], "total_shots_per_method": item["total_budget_per_method"],
               "primary": item["primary"], "exact_k3": a["exact"]}
        if mitigation:
            row.update(psa_k3=a["psa"], numerical_residual_bound=a["bounded_numerical_residual"],
                       equivalence_margin=a["margin"], status=a["status"], h2_decision=a["h2_decision"])
            for method in ("raw", "mitigated"):
                m = a["methods"][method]
                row[f"{method}_k3"] = m["estimate"]
                row[f"{method}_resolves"] = m["resolves"]
                for comparison, key in (("exact", "difference_exact_ci95_with_residual"),
                                        ("psa", "difference_psa_ci95")):
                    row[f"{method}_minus_{comparison}_ci95_low"] = m[key][0]
                    row[f"{method}_minus_{comparison}_ci95_high"] = m[key][1]
        else:
            row.update(aer_k3=a["estimate"], absolute_error=a["absolute_error"])
        rows.append(row)
    return rows


def ibm_rows(hardware: dict, backend: str, jobs: int) -> list[dict]:
    a = hardware["analysis"]
    return [{"method": name, "exact_k3": a["exact"], "psa_k3": a["psa"],
             "estimate_k3": result["estimate"], "minus_exact_ci95_low": result["difference_exact_ci95_with_residual"][0],
             "minus_exact_ci95_high": result["difference_exact_ci95_with_residual"][1],
             "minus_psa_ci95_low": result["difference_psa_ci95"][0],
             "minus_psa_ci95_high": result["difference_psa_ci95"][1],
             "resolves": result["resolves"], "h2_decision": a["h2_decision"],
             "blocks": hardware["complete_blocks"], "backend": backend, "hardware_jobs": jobs,
             "numerical_residual_bound": a["bounded_numerical_residual"]}
            for name, result in a["methods"].items()]


def h2_figure(path: Path, aer: dict, ibm: dict) -> None:
    cache = Path(__file__).resolve().parents[1] / "results" / "_cache"
    (cache / "matplotlib").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    exact = aer["exact"]
    points = [("Exato", exact, None, "#1f2937"),
              ("PSA · blocos locais", aer["psa"], None, "#2563eb"),
              ("PSA · blocos IBM", ibm["psa"], None, "#2563eb")]
    for label, analysis, key, color in (("Aer · bruto", aer, "raw", "#d97706"),
                                        ("Aer · mitigado", aer, "mitigated", "#7c3aed"),
                                        ("IBM · bruto", ibm, "raw", "#d97706"),
                                        ("IBM · mitigado", ibm, "mitigated", "#7c3aed")):
        method = analysis["methods"][key]
        low, high = method["difference_exact_ci95_with_residual"]
        points.append((label, method["estimate"], (analysis["exact"]+low, analysis["exact"]+high), color))
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    for index, (label, value, ci, color) in enumerate(points):
        y = len(points)-1-index
        if ci is None:
            ax.plot(value, y, "o", color=color, markersize=7)
        else:
            ax.errorbar(value, y, xerr=[[max(0., value-ci[0])], [max(0., ci[1]-value)]],
                        fmt="o", color=color, capsize=3, markersize=6)
    ax.axvline(exact, color="#9ca3af", linestyle="--", linewidth=1)
    ax.set_yticks(list(range(len(points))))
    ax.set_yticklabels([p[0] for p in reversed(points)])
    ax.set_xlabel("K₃ = correlação conectada Z₀Z₁Z₂ em τ = 2")
    ax.set_title("Caso principal: N = 4, μ = 3")
    ax.grid(axis="x", alpha=.2)
    fig.text(.12, .015, "Barras: IC 95% bootstrap para K₃ − exato, com limite numérico; PSA sem IC individual nesta figura.", fontsize=8)
    fig.subplots_adjust(left=.28, bottom=.17, right=.97, top=.88)
    fig.savefig(path.with_suffix(".pdf"))
    fig.savefig(path.with_suffix(".png"), dpi=220)
    plt.close(fig)


def prepare(study_path: Path, hardware_path: Path, output: Path) -> Path:
    study_path, hardware_path, output = study_path.resolve(), hardware_path.resolve(), output.resolve()
    results_root = study_path.parents[2]
    if not hardware_path.is_relative_to(results_root):
        raise ValueError("O relatório IBM deve estar no mesmo diretório results/ do estudo")
    study, phases, reports = phase_reports(study_path)
    hardware = read(hardware_path)
    if hardware["complete_blocks"] != hardware["expected_blocks"] or hardware["pending_jobs"]:
        raise ValueError("A coleta IBM não contém todos os blocos")
    primary = [c for c in reports["T07-mitigacao"]["endpoint_cases"] if c["primary"]]
    if len(primary) != 1 or abs(primary[0]["analysis"]["exact"]-hardware["analysis"]["exact"]) > 1e-8:
        raise ValueError("Os casos principais local e IBM não correspondem")
    hardware_protocol_path = Path(hardware["source_protocol"]).resolve()
    if hardware_protocol_path.parent != hardware_path.parent or hardware_protocol_path.name != "run.json":
        raise ValueError("O relatório IBM aponta para outro protocolo")
    hardware_run = read(hardware_protocol_path)
    hardware_spec = read(hardware_protocol_path.parent / "protocol.json")
    hardware_steps = [step for step in hardware_spec["steps"] if step["action"] == "hardware"]
    backends = {step["request"]["backend"] for step in hardware_steps}
    if hardware_run["status"] != "completed" or len(hardware_steps) != 80 or len(backends) != 1:
        raise ValueError("Protocolo IBM incompleto ou com backends diferentes")
    backend = backends.pop()
    if output.exists():
        raise FileExistsError(f"Pacote já existe: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".article-package-", dir=output.parent))
    try:
        tables = stage / "tables"
        reports_dir = stage / "reports"
        figures = stage / "figures"
        reports_dir.mkdir()
        figures.mkdir()
        sources = {}
        def record(path: Path):
            sources[str(path.resolve().relative_to(results_root))] = digest(path)
        record(study_path); record(hardware_path)
        for source, target in ((hardware_protocol_path, "IBM-protocol-run.json"),
                               (hardware_protocol_path.parent / "protocol.json", "IBM-protocol-spec.json")):
            record(source)
            shutil.copyfile(source, reports_dir / target)
        for name in PHASES:
            source = study_path.parent / name / "analysis.json"
            record(source)
            shutil.copyfile(source, reports_dir / f"{name}.json")
        for name in ("reference_checks.json", "trotter_recovery.json"):
            source = study_path.parent / name
            record(source)
            shutil.copyfile(source, reports_dir / name)
        for name in ("emenda_amostragem_v3.json", "emenda_discretizacao_v4.json"):
            source = study_path.parents[3] / "configs" / "protocols" / "artigo_v1" / "especificacoes" / name
            relative = str(source.relative_to(study_path.parents[3]))
            if digest(source) != study["environment"]["source_sha256"].get(relative):
                raise ValueError(f"Emenda versionada mudou após a execução: {relative}")
            shutil.copyfile(source, reports_dir / name)
        shutil.copyfile(hardware_path, reports_dir / "IBM-hardware-analysis.json")

        controls = []
        for name in PHASES:
            checks = reports[name]["checks"]
            controls.append({"phase": name, "execution_status": phases[name]["status"],
                             "analysis_status": reports[name]["status"], "checks": len(checks),
                             "failed_checks": sum(not c["pass"] for c in checks),
                             "scientific_hypothesis_not_an_acceptance_gate": True})
        write_csv(tables / "controls.csv", list(controls[0]), controls)
        benchmark = [{"name": c["name"], "max_abs": c["value"], "limit": c["limit"], "passed": c["pass"]}
                     for c in reports["T00-reproducao-publicada"]["checks"] if c["name"].startswith("Figura 2(c)")]
        write_csv(tables / "published_reproduction.csv", list(benchmark[0]), benchmark)
        sampling = [{"n": c["cell"]["n"], "mu": c["cell"]["mu"], "blocks": c["seeds"],
                     "trajectories_per_block": c["trajectories"], "max_standard_error_k3": c["max_seed_standard_error_c3"],
                     "limit": .01} for c in reports["T02-amostragem-suplementar"]["cases"]]
        write_csv(tables / "sampling_precision.csv", list(sampling[0]), sampling)
        for name, filename in (("T03-classica-principal", "h1_main.csv"),
                               ("T03-classica-extensao", "h1_extension.csv")):
            rows = h1_rows(reports[name]); write_csv(tables / filename, list(rows[0]), rows)
        measurements = []
        for c in reports["T05-medicoes"]["cases"]:
            if "shots_per_repetition" not in c:
                continue
            m = c["measured_c3"]
            measurements.append({"n": c["cell"]["n"], "mu": c["cell"]["mu"],
                                 "shots_per_block": c["shots_per_repetition"], "blocks": c["repetitions"],
                                 "total_shots_per_time": c["total_shots_per_time"],
                                 "k3_rmse": m["rmse"], "k3_normalized_rmse": m["normalized_rmse"]})
        write_csv(tables / "measurement_budget.csv", list(measurements[0]), measurements)
        for name, filename, mitigated in (("T06-ruido", "gate_noise.csv", False),
                                           ("T07-mitigacao", "mitigation.csv", True)):
            rows = endpoint_rows(reports[name], mitigated)
            write_csv(tables / filename, list(rows[0]), rows)
        ibm = ibm_rows(hardware, backend, len(hardware_steps))
        write_csv(tables / "ibm_primary.csv", list(ibm[0]), ibm)

        for name, n, mu in (("T03-classica-principal", 4, 3.0),
                            ("T03-classica-principal", 8, 3.0),
                            ("T03-classica-principal", 4, 10.0),
                            ("T03-classica-extensao", 16, 3.0),
                            ("T05-medicoes", 4, 3.0)):
            stem = f"n{n}_mu{mu}"
            for ext in ("csv", "png"):
                if n == 16 and ext == "csv":
                    continue  # A tabela H1 e a figura bastam; a curva completa está no arquivo bruto.
                matches = list((study_path.parent / name).glob(f"cell_*_{stem}.{ext}"))
                if len(matches) != 1:
                    raise ValueError(f"Figura esperada ausente: {name}, {stem}, {ext}")
                source = matches[0]
                record(source)
                target = figures / f"{name}_{stem}.{ext}"
                if ext == "csv":
                    target.write_bytes(source.read_bytes().replace(b"\r\n", b"\n"))
                else:
                    shutil.copyfile(source, target)
        h2_figure(figures / "h2_primary_comparison", primary[0]["analysis"], hardware["analysis"])
        write_notes(stage / "README.md", reports, primary[0], hardware, benchmark)
        manifest = {"schema_version": 1, "study_status": study["status"],
                    "study_source_fingerprint": study["environment"]["fingerprint"],
                    "generator_sha256": digest(Path(__file__)),
                    "hardware_status_original": hardware["scientific_status"],
                    "source_sha256": sources,
                    "package_files_sha256": {str(p.relative_to(stage)): digest(p) for p in sorted(stage.rglob("*")) if p.is_file()}}
        (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return output


def write_notes(path: Path, reports: dict, primary: dict, hardware: dict, benchmark: list[dict]) -> None:
    main = h1_rows(reports["T03-classica-principal"])
    extension = h1_rows(reports["T03-classica-extensao"])
    qiskit_max = max(c["value"] for c in reports["T04-qiskit"]["checks"])
    exact_max = max(c["max_abs"] for c in benchmark if ": exact " in c["name"])
    psa_max = max(c["max_abs"] for c in benchmark if ": psa " in c["name"])
    aer = primary["analysis"]
    ibm = hardware["analysis"]
    content = f"""# Pacote de resultados para o artigo

Este pacote resume o estudo local concluído e os 20 blocos IBM já coletados.
`manifest.json` contém SHA-256 dos relatórios originais e dos arquivos derivados.
O diretório original `results/` completo continua necessário para reproduzir cada execução.

## Ordem de leitura

1. `tables/controls.csv` e `tables/published_reproduction.csv`: validade numérica e reprodução da Figura 2(c).
2. `tables/h1_main.csv`: comparação principal da PSA com o exato para K₂ e K₃, N=4/6/8.
3. `tables/measurement_budget.csv`: efeito de 1.024, 4.096 e 16.384 shots no circuito ideal.
4. `tables/mitigation.csv` e `tables/ibm_primary.csv`: avaliação do caso H2 predefinido.
5. `tables/h1_extension.csv`, `tables/gate_noise.csv` e `tables/sampling_precision.csv`: material suplementar e sensibilidade.
6. `figures/`: curvas originais selecionadas e comparação estática do caso H2.

## Onde usar no artigo

- **Métodos e validação:** reprodução publicada (T00), controles de integração e amostragem (T01/T02), Trotter e equivalência Qiskit (T04), emendas documentadas.
- **Resultado principal H1:** `h1_main.csv` e curvas de N=4/8. Use R₂, R₃ e IC95 de R₃−R₂ por célula; descreva o padrão sem extrapolar o ponto de quebra para N maior.
- **Efeito do orçamento de medição:** `measurement_budget.csv` e curva T05 N=4, μ=3.
- **Resultado principal H2:** `mitigation.csv`, `ibm_primary.csv` e `h2_primary_comparison.pdf`. Separe o circuito ideal, o Aer ruidoso e a QPU real.
- **Suplemento:** extensão N=12/16, grade completa de ruído, precisão de amostragem, arquivos JSON completos e protocolo IBM.

## Resultados que o texto pode afirmar

- Reprodução publicada: maior desvio exato {exact_max:.6g} (limite 0,02) e PSA {psa_max:.6g} (limite 0,06). São coordenadas digitalizadas da figura, não dados brutos dos autores.
- H1: o IC95 de R₃−R₂ é positivo em {sum(r['ci_positive'] for r in main)}/{len(main)} células principais; N=4, μ=0,1 não resolve o sinal. A extensão N=12/16 tem {sum(r['ci_positive'] for r in extension)}/{len(extension)} ICs positivos. Esses resultados são por célula; tendências e multiplicidade exigem interpretação separada.
- O teste principal H2 é N=4, μ=3, τ=2, trio (0,1,2), 20 blocos e 16.384 shots por bloco/método. K₃ exato = {aer['exact']:.6f}; PSA local = {aer['psa']:.6f}; Aer bruto = {aer['methods']['raw']['estimate']:.6f}; Aer mitigado = {aer['methods']['mitigated']['estimate']:.6f}. Decisão: **{aer['h2_decision']}**.
- Na IBM, K₃ bruto = {ibm['methods']['raw']['estimate']:.6f}; mitigado = {ibm['methods']['mitigated']['estimate']:.6f}; decisão = **{ibm['h2_decision']}**. Há {hardware['complete_blocks']} blocos completos e nenhum job pendente no registro. O status textual do arquivo IBM permanece `{hardware['scientific_status']}` porque ele foi calculado antes da conclusão local; o arquivo original não foi reescrito.

## Interpretação e limites

`passed` nos controles significa que o protocolo e as verificações numéricas passaram; não significa que H2 foi confirmada. No caso principal, as estimativas Aer/IBM ficam perto de zero e os ICs para a diferença ao exato não cabem na margem de equivalência ±0,01. A mitigação de leitura usada aqui não recuperou K₃ exato. Registre essa conclusão, sem afirmar vantagem quântica.

A grade de ruído em μ=10, τ=4 foi refinada para 29 pontos/448 passos Trotter; o limite ideal de erro permaneceu 0,001. A emenda amostral v3 e a emenda temporal v4 estão em `reports/`. A comparação entre células de ruído deve declarar a diferença de profundidade.

A condição inicial de precisão amostral não passou e foi substituída pela emenda v3 após a observação dessa falha. A emenda v4 também foi definida depois da falha de Trotter. Declare ambas como alterações posteriores ao protocolo inicial, com os resultados anteriores preservados.

As inclinações agregadas H1 de N=8/12/16 têm estimativa pontual fora do IC percentil bootstrap registrado. Não use essas inclinações como resultado confirmatório sem revisar o viés/intervalo e a multiplicidade. As tabelas por célula são o ponto de partida para essa auditoria.

O maior desvio Qiskit versus emulador no controle T04 foi {qiskit_max:.3g} (limite 1e-10). A coleção IBM é uma aquisição antecipada separada da T07; os relatórios completos em `reports/` guardam ICs, orçamento, sementes e decisões.

## Como regenerar

Na raiz do repositório, execute `python analysis/prepare_article_package.py CAMINHO/study.json CAMINHO/hardware_analysis.json --output NOVO_DIRETORIO`. O destino deve estar vazio. O pacote é um recorte de escrita, não substitui o arquivo científico integral de `results/`.
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path, help="study.json final")
    parser.add_argument("hardware", type=Path, help="hardware_analysis.json da coleta IBM")
    parser.add_argument("--output", type=Path, help="diretório novo para o pacote")
    args = parser.parse_args()
    output = args.output or Path("results/article_packages") / args.study.parent.name
    print(prepare(args.study, args.hardware, output))


if __name__ == "__main__":
    main()
