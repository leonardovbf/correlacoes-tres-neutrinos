#!/usr/bin/env python3
"""Audita a repetição de contagens e a saturação da fase T07 sem alterar a coleta."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from app.backend import audit, protocol
from neutrinos.qiskit_backend import build_trotter_circuit
from neutrinos.sim import ExperimentConfig


DEFAULT_RUN = ROOT / "results/protocols/20261106T121711Z-b4a6da31f7d4/run.json"
DEFAULT_REPORT = ROOT / "analysis/audits/aer_saturation_20261106.json"
PACKAGED_T07 = ROOT / "analysis/article_packages/20261106T120036Z-7f9b932d0594/reports/T07-mitigacao.json"


def density_check(config: ExperimentConfig, steps: int, interval_index: int) -> dict:
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    basis = ["rz", "sx", "x", "cx"]
    circuit = build_trotter_circuit(config, float(config.times[interval_index]),
                                    steps * interval_index)
    compiled = transpile(circuit, basis_gates=basis, optimization_level=1,
                         seed_transpiler=config.seed)
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(.001, 1), ["sx", "x"])
    model.add_all_qubit_quantum_error(depolarizing_error(.01, 2), "cx")
    compiled.save_density_matrix()
    simulator = AerSimulator(noise_model=model, basis_gates=basis, method="density_matrix")
    rho = np.asarray(simulator.run(compiled, shots=1).result().data(0)["density_matrix"])
    dim = 1 << config.n
    return {"mu": config.mu, "tau": float(config.times[interval_index]),
            "steps_per_interval": steps, "total_steps": steps * interval_index,
            "cx_count": int(compiled.count_ops().get("cx", 0)),
            "max_diagonal_distance_from_uniform": float(np.max(np.abs(np.real(np.diag(rho)) - 1 / dim))),
            "frobenius_distance_from_maximally_mixed": float(np.linalg.norm(rho - np.eye(dim) / dim)),
            "scope": "Sem ruído de leitura; verificação determinística da matriz densidade antes das medições."}


def analyze(run_path: Path, *, include_density: bool = True) -> dict:
    run_path = run_path.resolve()
    root = run_path.parents[2]
    record = json.loads(run_path.read_text())
    spec_path = run_path.parent / "protocol.json"
    spec = protocol.read_protocol(spec_path)
    if record["status"] != "completed" or spec.name != "T07-mitigacao":
        raise ValueError("Informe o run.json completo da fase T07-mitigacao")
    if len(record["steps"]) != len(spec.steps):
        raise ValueError("O registro e o protocolo possuem quantidades de etapas diferentes")
    references = {step.id: step.request["config"] for step in spec.steps if step.action == "classical"}
    groups = defaultdict(list)
    representative = {}
    for step, state in zip(spec.steps, record["steps"], strict=True):
        if step.action != "mitigation":
            continue
        if state["status"] != "completed":
            raise ValueError(f"Etapa não concluída: {step.id}")
        request = step.request
        if request["single_qubit_error"] not in (.0001, .001):
            continue
        profile = "moderado" if request["single_qubit_error"] == .001 else "leve"
        config = ExperimentConfig.from_dict(references[step.run_from])
        tau = float(config.times[request["interval_index"]])
        cell = (config.mu, tau)
        execution = audit.load_execution(root, state["execution_id"])
        protocol.verify_artifacts(root, execution)
        result = json.loads((root / execution["result"]["path"]).read_text())
        moments = next(root / item["path"] for item in execution["artifacts"]
                       if item["path"].endswith("/moments.npz"))
        with np.load(moments, allow_pickle=False) as arrays:
            raw = arrays[result["counts_keys"]["raw"]].copy()
            signal = arrays[result["counts_keys"]["signal"]].copy()
            exact = float(arrays["exact_c3"][request["interval_index"], 0])
        group = (profile, request["shots"])
        groups[group].append({"seed": config.seed, "cell": cell,
                              "raw_hash": hashlib.sha256(raw.tobytes()).hexdigest(),
                              "signal_hash": hashlib.sha256(signal.tobytes()).hexdigest(),
                              "simulator_seed": result["metadata"]["raw"]["seed_simulator"],
                              "raw_tv_uniform": float(.5 * np.abs(raw / raw.sum() - 1 / len(raw)).sum()),
                              "exact_c3": exact,
                              "raw_c3": result["raw"],
                              "mitigated_c3": result["mitigated"],
                              "cx_count": result["metadata"]["raw"]["cx_count"]})
        if profile == "moderado" and config.seed == 40001 and cell in ((.1, 1.), (3., 2.)):
            representative[cell] = (config, request["steps"], request["interval_index"])
    summary = {}
    for (profile, shots), rows in sorted(groups.items()):
        seeds = sorted({row["seed"] for row in rows})
        cells = sorted({row["cell"] for row in rows})
        per_seed_raw = {seed: len({row["raw_hash"] for row in rows if row["seed"] == seed})
                        for seed in seeds}
        per_seed_signal = {seed: len({row["signal_hash"] for row in rows if row["seed"] == seed})
                           for seed in seeds}
        per_seed_simulator = {seed: len({row["simulator_seed"] for row in rows if row["seed"] == seed})
                              for seed in seeds}
        key = f"{profile}_{shots}"
        summary[key] = {"cells": len(cells), "independent_seed_blocks": len(seeds),
                        "executions": len(rows),
                        "distinct_raw_c3_across_cells_and_seeds_pooled": len({row["raw_c3"] for row in rows}),
                        "distinct_mitigated_c3_across_cells_and_seeds_pooled": len({row["mitigated_c3"] for row in rows}),
                        "distinct_raw_count_vectors_per_seed": per_seed_raw,
                        "distinct_signal_count_vectors_per_seed": per_seed_signal,
                        "distinct_raw_count_vectors_across_all_executions": len({row["raw_hash"] for row in rows}),
                        "distinct_signal_count_vectors_across_all_executions": len({row["signal_hash"] for row in rows}),
                        "same_simulator_seed_across_cells_per_block": all(n == 1 for n in per_seed_simulator.values()),
                        "all_seeds_same_raw_counts_across_cells": all(n == 1 for n in per_seed_raw.values()),
                        "all_seeds_same_signal_counts_across_cells": all(n == 1 for n in per_seed_signal.values()),
                        "raw_tv_uniform_min": min(row["raw_tv_uniform"] for row in rows),
                        "raw_tv_uniform_max": max(row["raw_tv_uniform"] for row in rows),
                        "exact_c3_min": min(row["exact_c3"] for row in rows),
                        "exact_c3_max": max(row["exact_c3"] for row in rows),
                        "cx_count_unique": sorted({row["cx_count"] for row in rows})}
    packaged = json.loads(PACKAGED_T07.read_text())
    endpoint_summary = {}
    for key in summary:
        profile, budget = key.split("_")
        parameters = ((.001, .01, .03) if profile == "moderado" else (.0001, .001, .01))
        entries = [row for row in packaged["endpoint_cases"]
                   if row["cell"]["shots"] == int(budget)
                   and (row["cell"]["single"], row["cell"]["two"], row["cell"]["readout"]) == parameters]
        endpoint_summary[key] = {
            "cells": len(entries),
            "distinct_raw_estimates": len({row["analysis"]["methods"]["raw"]["estimate"] for row in entries}),
            "distinct_mitigated_estimates": len({row["analysis"]["methods"]["mitigated"]["estimate"] for row in entries}),
            "raw_estimate_if_repeated": (entries[0]["analysis"]["methods"]["raw"]["estimate"]
                                         if len({row["analysis"]["methods"]["raw"]["estimate"] for row in entries}) == 1 else None),
            "mitigated_estimate_if_repeated": (entries[0]["analysis"]["methods"]["mitigated"]["estimate"]
                                               if len({row["analysis"]["methods"]["mitigated"]["estimate"] for row in entries}) == 1 else None),
        }
    checks = []
    if include_density:
        for cell in ((.1, 1.), (3., 2.)):
            if cell not in representative:
                raise ValueError(f"Configuração representativa ausente: {cell}")
            checks.append(density_check(*representative[cell]))
    return {"schema_version": 1, "source_run": str(run_path),
            "source_run_sha256": audit.file_hash(run_path),
            "source_protocol_sha256": audit.file_hash(spec_path),
            "source_packaged_T07_sha256": audit.file_hash(PACKAGED_T07),
            "status": "analyzed", "profile": "auditoria_pos_coleta_sem_modificar_resultados",
            "groups": summary, "published_endpoint_estimates": endpoint_summary,
            "density_matrix_checks": checks,
            "interpretation": "Contagens idênticas entre células com a mesma semente decorrem da saturação numérica da saída próxima do estado maximamente misto. Os 20 blocos de sementes distintas permanecem independentes dentro de cada célula; células que reutilizam os mesmos vetores não são amostras independentes entre si.",
            "caveat": "Os dois testes determinísticos de matriz densidade são representativos, não uma prova de ausência de qualquer erro de implementação."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--skip-density-check", action="store_true")
    args = parser.parse_args()
    result = analyze(args.run, include_density=not args.skip_density_check)
    audit.atomic_json(args.output, result)
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
