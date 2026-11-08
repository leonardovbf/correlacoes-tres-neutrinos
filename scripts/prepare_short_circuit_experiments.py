#!/usr/bin/env python3
"""Define, valida e prepara a extensão exploratória de circuitos curtos.

Nenhum subcomando deste arquivo envia jobs. O protocolo IBM gerado só pode ser
executado pelo runner com a opção explícita --allow-hardware.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from app.backend import audit, ibm_runtime, protocol, service
from app.backend.storage import RunStore
from neutrinos.qiskit_backend import first_interval_probabilities, build_trotter_circuit
from neutrinos.sim import (ExperimentConfig, MomentSeries, classical_exact, observable_from_counts,
                           quantum_trotter, trotter_probabilities)


DESIGN_DIR = ROOT / "configs" / "protocols" / "circuitos_curtos_v2"
LOCAL_SEEDS = range(70001, 70021)
SCREEN_SEEDS = range(80001, 80006)
CANDIDATES = {"principal_2passos": {"steps": 2, "scope": "trio_012"},
              "todos_6passos": {"steps": 6, "scope": "todos_os_trios"}}
NOISE = {"leve": {"single_qubit_error": .0001, "two_qubit_error": .001, "readout_error": .01},
         "moderado": {"single_qubit_error": .001, "two_qubit_error": .01, "readout_error": .03}}


def config(seed: int) -> dict:
    return {"n": 4, "mu": 3., "theta": .2, "t_max": 1.5, "points": 2,
            "seed": seed, "flavors": [0, 0, 1, 1],
            "omega_values": [.7, .9, 1.1, 1.3],
            "g_values": [[float(i != j) for j in range(4)] for i in range(4)]}


def design() -> dict:
    return {
        "schema_version": 1, "name": "circuitos_curtos_v2",
        "scientific_status": "nova_extensao_exploratoria_pos_resultados_v1",
        "source": "Resultados v1 preservados; tau=1.5 foi escolhido depois de inspecionar a grade anterior.",
        "model": config(70001), "primary_observable": {"kind": "c3", "trio": [0, 1, 2], "tau": 1.5},
        "candidates": CANDIDATES,
        "ideal_limit": .001, "qiskit_probability_limit": 1e-10,
        "local": {"psa_seeds": list(LOCAL_SEEDS), "trajectories_per_seed": 4096,
                  "rk4_substeps": 12, "measurement_shots_per_seed": 4096,
                  "aer_seeds": list(range(70001, 70006)), "aer_profiles": NOISE,
                  "interpretation": "Aer usa ruido despolarizante generico; nao representa a calibracao IBM."},
        "hardware_screen": {"seeds": list(SCREEN_SEEDS), "backend": "definir_ao_preparar",
                            "optimization_level": 3, "transpiler_seed": 81001,
                            "arms": ["sem_supressao", "gate_twirling"],
                            "shots_per_job": 4096, "planned_jobs": 20,
                            "total_shots": 81920,
                            "role": "triagem_exploratoria; nenhuma conclusao confirmatoria H2"},
        "confirmation": {"seeds": list(range(90001, 90021)),
                         "selection_rule": "Escolher antes da confirmacao um candidato e um braco pela menor distancia absoluta ao exato na triagem; empates favorecem menos passos e sem twirling.",
                         "shots_per_job": 16384, "planned_jobs": 20, "total_shots": 327680,
                         "decision": "Suporte a superioridade neste ponto somente se o IC95 bootstrap por blocos de D=|K3_IBM-K3_exato|-|K3_PSA-K3_exato| tiver limite superior <0 e o IC95 de K3_IBM-K3_PSA excluir zero. Usar 2000 replicas; nao reutilizar sementes nem contagens da triagem."},
        "limitations": ["O teste v1 em tau=2 permanece inconclusivo.",
                        "A escolha de tau=1.5 e dos circuitos e exploratoria.",
                        "Mais shots nao removem vies de portas."]}


def local_protocol() -> protocol.ProtocolSpec:
    steps = []
    for seed in LOCAL_SEEDS:
        parent = f"curto_s{seed}"
        steps.append({"id": parent, "action": "classical", "request": {
            "config": config(seed), "trajectories": 4096, "substeps": 12}})
        for candidate, values in CANDIDATES.items():
            nsteps = values["steps"]
            steps.append({"id": f"{parent}_{candidate}_ideal", "action": "quantum",
                          "run_from": parent, "request": {"steps": nsteps, "shots": 4096,
                                                         "readout_error": 0.}})
            if seed == LOCAL_SEEDS.start:
                steps.append({"id": f"{parent}_{candidate}_qiskit", "action": "circuit",
                              "run_from": parent, "request": {"steps": nsteps, "interval_index": 1}})
            if seed < 70006:
                for noise_name, errors in NOISE.items():
                    steps.append({"id": f"{parent}_{candidate}_{noise_name}", "action": "aer",
                                  "run_from": parent, "request": {"steps": nsteps,
                                      "interval_index": 1, "shots": 4096, "kind": "c3", "index": 0,
                                      **errors}})
    return protocol.ProtocolSpec(name="T09-circuitos-curtos-local-v2", steps=steps,
        description="Extensao exploratoria independente da v1: N4, mu3, tau1.5, PSA sementes 70001-70020; circuitos 2/6 passos; Aer leve/moderado em 5 sementes. Nenhum hardware.")


def definitions(check: bool) -> list[str]:
    files = {DESIGN_DIR / "design.json": design(),
             DESIGN_DIR / "local_protocol.json": local_protocol().model_dump(mode="json")}
    differences = []
    for path, value in files.items():
        payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if check:
            if not path.exists() or path.read_text() != payload:
                differences.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload)
    return differences


def protocol_digest(spec: protocol.ProtocolSpec) -> str:
    return hashlib.sha256(json.dumps(spec.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


def ideal_preflight() -> dict:
    cfg = ExperimentConfig.from_dict(config(70001))
    exact = classical_exact(cfg)
    cases = {}
    for name, candidate in CANDIDATES.items():
        steps = candidate["steps"]
        ideal, _ = quantum_trotter(cfg, steps, 32, 0.)
        _, qiskit_probabilities = first_interval_probabilities(cfg, steps, 1)
        emulator_probabilities, _ = trotter_probabilities(cfg, steps)
        all_errors = np.abs(exact.c3[-1] - ideal.c3[-1])
        selected = float(all_errors[0] if candidate["scope"] == "trio_012" else all_errors.max())
        qiskit_error = float(np.max(np.abs(qiskit_probabilities - emulator_probabilities[-1])))
        cases[name] = {"steps": steps, "scope": candidate["scope"],
                       "exact_c3_trio012": float(exact.c3[-1, 0]),
                       "ideal_c3_trio012": float(ideal.c3[-1, 0]),
                       "primary_c3_error": float(all_errors[0]),
                       "all_trios_max_c3_error": float(all_errors.max()),
                       "qiskit_probability_error": qiskit_error,
                       "pass": selected <= .001 and qiskit_error <= 1e-10}
    return {"status": "passed" if all(c["pass"] for c in cases.values()) else "failed",
            "scientific_status": "exploratory_new_protocol", "cases": cases,
            "ibm_jobs_submitted": 0}


def prepare_hardware(backend_name: str, local_record: Path, output: Path, max_depth: int) -> dict:
    from qiskit import qpy
    from qiskit.transpiler import generate_preset_pass_manager

    preflight = ideal_preflight()
    if preflight["status"] != "passed":
        raise ValueError("Validação ideal/Qiskit falhou; nenhuma fila preparada")
    root = output.resolve()
    source = local_record.resolve()
    if source.parent.parent != root / "protocols":
        raise ValueError("Registro local deve estar no mesmo --output")
    record = json.loads(source.read_text())
    if record.get("status") != "completed" or record.get("name") != "T09-circuitos-curtos-local-v2":
        raise ValueError("Conclua o protocolo local v2 antes de preparar a IBM")
    if record.get("protocol_sha256") != protocol_digest(local_protocol()):
        raise ValueError("O protocolo local concluído não corresponde à definição v2")
    local_analysis_path = source.parent / "short_circuit_local_analysis.json"
    if not local_analysis_path.exists():
        raise ValueError("Execute analyze-local e examine o relatório antes de preparar a IBM")
    local_analysis = json.loads(local_analysis_path.read_text())
    if local_analysis.get("status") != "analyzed" or local_analysis.get("source_protocol_sha256") != audit.file_hash(source):
        raise ValueError("Relatório local incompleto ou incompatível com o protocolo")
    for step in record["steps"]:
        if step["action"] == "circuit":
            execution = audit.load_execution(root, step["execution_id"])
            result = json.loads((root / execution["result"]["path"]).read_text())
            if result["max_probability_difference"] > 1e-10:
                raise ValueError("Controle Qiskit local falhou")
    cloud = ibm_runtime._service()
    backend = cloud.backend(backend_name)
    if backend.num_qubits < 4 or not backend.status().operational or getattr(backend.configuration(), "simulator", False):
        raise ValueError("Selecione backend IBM físico operacional com pelo menos 4 qubits")
    folder = root / "short-circuit-preparations" / audit.new_id()
    folder.mkdir(parents=True)
    cfg = ExperimentConfig.from_dict(config(80001))
    previews = {}
    layouts = {}
    for name, candidate in CANDIDATES.items():
        circuit = build_trotter_circuit(cfg, 1.5, candidate["steps"])
        circuit.measure_all()
        first = generate_preset_pass_manager(backend=backend, optimization_level=3,
                 seed_transpiler=81001).run(circuit)
        layout = first.layout.initial_index_layout(filter_ancillas=True)
        compiled = generate_preset_pass_manager(backend=backend, optimization_level=3,
                 seed_transpiler=81001, initial_layout=layout).run(circuit)
        two_qubit = sum(count for gate, count in compiled.count_ops().items()
                        if gate in {"cx", "cz", "ecr", "rzz", "rxx", "ryy"})
        if compiled.depth() > max_depth or two_qubit >= 672:
            raise ValueError(f"{name}: circuito compilado profundo demais ({compiled.depth()} camadas, {two_qubit} portas de dois qubits)")
        binary = io.BytesIO()
        qpy.dump(compiled, binary)
        qpy_path = folder / f"{name}.qpy"
        qpy_path.write_bytes(binary.getvalue())
        layouts[name] = layout
        previews[name] = {"steps": candidate["steps"], "depth": compiled.depth(),
                          "two_qubit_gates": two_qubit, "initial_layout": layout,
                          "physical_qubits": compiled.layout.final_index_layout(),
                          "qpy_file": qpy_path.name, "qpy_sha256": audit.file_hash(qpy_path)}
    steps = []
    for name, candidate in CANDIDATES.items():
        for seed in SCREEN_SEEDS:
            parent = f"{name}_s{seed}"
            steps.append({"id": parent, "action": "classical", "request": {
                "config": config(seed), "trajectories": 4096, "substeps": 12}})
            steps.append({"id": parent + "_ideal", "action": "quantum", "run_from": parent,
                          "request": {"steps": candidate["steps"], "shots": 32, "readout_error": 0.}})
            for arm, twirling in (("plain", False), ("twirled", True)):
                steps.append({"id": parent + "_" + arm, "action": "hardware", "run_from": parent,
                              "request": {"backend": backend_name, "interval_index": 1,
                                  "steps": candidate["steps"], "shots": 4096,
                                  "kind": "c3", "index": 0, "role": "raw",
                                  "initial_layout": layouts[name], "max_depth": max_depth,
                                  "transpiler_seed": 81001, "optimization_level": 3,
                                  "gate_twirling": twirling}})
    spec = protocol.ProtocolSpec(name="T10-circuitos-curtos-IBM-triagem-v2", steps=steps,
        description="Triagem exploratoria separada da H2 v1: N4 mu3 tau1.5, dois circuitos x dois bracos x cinco sementes, 20 jobs/81920 shots. Sem calibracao de leitura; nenhum resultado e confirmatorio.")
    protocol_path = folder / "hardware_screen_protocol.json"
    audit.atomic_json(protocol_path, spec.model_dump(mode="json"))
    plan = {"schema_version": 1, "status": "prepared_not_submitted",
            "scientific_status": "exploratory_new_protocol", "backend": backend_name,
            "source_local_record": str(source), "source_local_sha256": audit.file_hash(source),
            "source_local_analysis_sha256": audit.file_hash(local_analysis_path),
            "design_sha256": audit.file_hash(DESIGN_DIR / "design.json"),
            "preflight": preflight, "previews": previews,
            "protocol_path": str(protocol_path), "protocol_sha256": audit.file_hash(protocol_path),
            "planned_jobs": 20, "total_shots": 81920, "ibm_jobs_submitted": 0,
            "prepared_utc": audit.utc_now()}
    audit.atomic_json(folder / "plan.json", plan)
    return plan


def _pooled_psa(blocks: list[dict], positions: np.ndarray) -> float:
    cfg = ExperimentConfig.from_dict(config(80001))
    moments = [np.mean([blocks[int(i)][name] for i in positions], axis=0)[None, :]
               for name in ("m1", "m2", "m3")]
    series = MomentSeries(np.array([1.5]), *moments, cfg.pair_index, cfg.trio_index,
                          "psa_pooled", {})
    return float(series.c3[0, 0])


def _analyze_arm(blocks: list[dict], *, repetitions: int, seed: int) -> dict:
    counts = np.sum([block["counts"] for block in blocks], axis=0)
    exact = blocks[0]["exact"]
    psa = _pooled_psa(blocks, np.arange(len(blocks)))
    estimate = float(observable_from_counts(counts, "c3", (0, 1, 2)))
    rng = np.random.default_rng(seed)
    differences = np.empty((repetitions, 3))
    for repetition in range(repetitions):
        positions = rng.integers(0, len(blocks), size=len(blocks))
        sampled = np.sum([rng.multinomial(int(blocks[int(i)]["counts"].sum()),
                           blocks[int(i)]["counts"] / blocks[int(i)]["counts"].sum())
                          for i in positions], axis=0)
        quantum = float(observable_from_counts(sampled, "c3", (0, 1, 2)))
        classical = _pooled_psa(blocks, positions)
        differences[repetition] = (quantum - exact, quantum - classical,
                                   abs(quantum - exact) - abs(classical - exact))
    intervals = np.percentile(differences, [2.5, 97.5], axis=0).T.tolist()
    advantage = abs(estimate - exact) - abs(psa - exact)
    return {"blocks": len(blocks), "shots": int(counts.sum()), "exact": exact,
            "psa": psa, "ibm": estimate, "difference_exact_ci95": intervals[0],
            "difference_psa_ci95": intervals[1], "advantage_D": advantage,
            "advantage_D_ci95": intervals[2], "bootstrap_repetitions": repetitions,
            "bootstrap_seed": seed,
            "bootstrap_unit": "reamostragem conjunta de blocos PSA e contagens multinomiais"}


def analyze_local(record_path: Path, output: Path) -> dict:
    root = output.resolve()
    record_path = record_path.resolve()
    if record_path.parent.parent != root / "protocols":
        raise ValueError("Use o mesmo --output do protocolo local")
    record = json.loads(record_path.read_text())
    if record.get("name") != "T09-circuitos-curtos-local-v2" or record.get("status") != "completed":
        raise ValueError("Informe um run.json local v2 concluído")
    if record.get("protocol_sha256") != protocol_digest(local_protocol()):
        raise ValueError("O protocolo local não corresponde à definição v2")
    psa_by_seed = {}
    groups: dict[str, list[dict]] = {}
    ideal = {}
    qiskit = {}
    for state in record["steps"]:
        execution = audit.load_execution(root, state["execution_id"])
        protocol.verify_artifacts(root, execution)
        result = json.loads((root / execution["result"]["path"]).read_text())
        moments = next(root / item["path"] for item in execution["artifacts"]
                       if item["path"].endswith("/moments.npz"))
        seed = int(state["id"].split("_s", 1)[1][:5])
        if state["action"] == "circuit":
            qiskit[state["id"]] = result["max_probability_difference"]
            continue
        with np.load(moments, allow_pickle=False) as arrays:
            if state["action"] == "classical":
                psa_by_seed[seed] = {name: arrays[f"psa_{name}"][1].copy()
                                     for name in ("m1", "m2", "m3")}
                continue
            candidate = next(name for name in CANDIDATES if name in state["id"])
            if state["action"] == "quantum":
                key = candidate + "/measured_ideal"
                counts = arrays["measured_counts"][1].copy()
                ideal[candidate] = result["quantum"]["ideal"]["c3"][1][0]
            elif state["action"] == "aer":
                noise_name = next(name for name in NOISE if state["id"].endswith(name))
                key = candidate + "/aer_" + noise_name
                counts = arrays[result["counts_key"]].copy()
            else:
                continue
            groups.setdefault(key, []).append({**psa_by_seed[seed], "counts": counts,
                "exact": float(arrays["exact_c3"][1, 0]), "seed": seed})
    if max(qiskit.values(), default=float("inf")) > 1e-10:
        raise ValueError("Controle independente Qiskit falhou")
    report = {"schema_version": 1, "status": "analyzed", "source_protocol": str(record_path),
              "source_protocol_sha256": audit.file_hash(record_path),
              "scientific_status": "exploratory_local_screen", "qiskit_probability_errors": qiskit,
              "ideal_c3_trio012": ideal, "arms": {}, "ibm_jobs_submitted": 0}
    for offset, (key, blocks) in enumerate(sorted(groups.items())):
        expected = 20 if key.endswith("measured_ideal") else 5
        if len(blocks) != expected or len({block["seed"] for block in blocks}) != expected:
            raise ValueError(f"{key}: blocos locais incompletos ou duplicados")
        report["arms"][key] = _analyze_arm(blocks, repetitions=2000, seed=91001 + offset)
    if len(report["arms"]) != 6:
        raise ValueError("Protocolo local sem os seis braços esperados")
    audit.atomic_json(record_path.parent / "short_circuit_local_analysis.json", report)
    return report


def collect_hardware(record_path: Path, output: Path) -> dict:
    record_path = record_path.resolve()
    root = output.resolve()
    if record_path.parent.parent != root / "protocols":
        raise ValueError("Use o mesmo --output da coleta IBM")
    record = json.loads(record_path.read_text())
    if record["name"] not in {"T10-circuitos-curtos-IBM-triagem-v2",
                               "T11-circuitos-curtos-IBM-confirmacao-v2"}:
        raise ValueError("Informe um protocolo IBM de circuitos curtos v2")
    if record["status"] != "completed":
        raise ValueError("Conclua primeiro todos os envios do protocolo")
    grouped: dict[str, list[dict]] = {}
    pending = []
    with ibm_runtime.shared_session():
        for state in record["steps"]:
            if state["action"] != "hardware":
                continue
            execution = audit.load_execution(root, state["execution_id"])
            protocol.verify_artifacts(root, execution)
            original = json.loads((root / execution["result"]["path"]).read_text())["hardware_runs"][-1]
            refreshed = service.refresh_hardware(state["run_id"], original["job_id"])
            if refreshed["status"] != "DONE":
                pending.append({"job_id": original["job_id"], "status": refreshed["status"]})
                continue
            manifest, _, arrays = service.store.load(state["run_id"])
            candidate = next(name for name, values in CANDIDATES.items()
                             if values["steps"] == original["steps"])
            arm = "twirled" if original.get("gate_twirling") else "plain"
            key = candidate + "/" + arm
            grouped.setdefault(key, []).append({
                "counts": arrays[refreshed["counts_key"]],
                "m1": arrays["psa_m1"][1], "m2": arrays["psa_m2"][1],
                "m3": arrays["psa_m3"][1], "exact": float(arrays["exact_c3"][1, 0]),
                "seed": manifest["config_input"]["seed"]})
    expected = len(SCREEN_SEEDS) if record["name"].startswith("T10") else 20
    complete = not pending and all(len(blocks) == expected for blocks in grouped.values())
    expected_arms = 4 if record["name"].startswith("T10") else 1
    complete = complete and len(grouped) == expected_arms
    failed = any(item["status"] in {"ERROR", "CANCELLED"} for item in pending)
    report = {"schema_version": 1, "source_protocol": str(record_path),
              "source_protocol_sha256": audit.file_hash(record_path),
              "status": "analyzed" if complete else "failed_jobs" if failed else "awaiting_jobs",
              "pending_jobs": pending, "complete_blocks_by_arm": {k: len(v) for k, v in grouped.items()},
              "expected_blocks_per_arm": expected, "scientific_status": (
                  "exploratory_screen" if record["name"].startswith("T10") else "independent_confirmation"),
              "arms": {}, "utc": audit.utc_now()}
    if complete:
        for offset, (key, blocks) in enumerate(sorted(grouped.items())):
            if len({block["seed"] for block in blocks}) != expected:
                raise ValueError(f"{key}: blocos não têm sementes independentes")
            report["arms"][key] = _analyze_arm(blocks, repetitions=2000, seed=92001 + offset)
        if record["name"].startswith("T10"):
            selected = min(report["arms"], key=lambda key: (
                abs(report["arms"][key]["ibm"] - report["arms"][key]["exact"]),
                CANDIDATES[key.split("/")[0]]["steps"], key.endswith("twirled")))
            report["selected_for_confirmation"] = selected
        else:
            arm = next(iter(report["arms"].values()))
            low, high = arm["difference_psa_ci95"]
            report["decision"] = ("supports_better_than_psa_at_this_endpoint"
                                   if arm["advantage_D_ci95"][1] < 0 and (high < 0 or low > 0)
                                   else "not_demonstrated")
    audit.atomic_json(record_path.parent / "short_circuit_hardware_analysis.json", report)
    return report


def prepare_confirmation(screen_record: Path, output: Path) -> dict:
    from qiskit import qpy
    from qiskit.transpiler import generate_preset_pass_manager

    root = output.resolve()
    screen_record = screen_record.resolve()
    if screen_record.parent.parent != root / "protocols":
        raise ValueError("Use o mesmo --output da triagem")
    record = json.loads(screen_record.read_text())
    if record.get("name") != "T10-circuitos-curtos-IBM-triagem-v2":
        raise ValueError("Informe o run.json da triagem v2")
    analysis_path = screen_record.parent / "short_circuit_hardware_analysis.json"
    analysis = json.loads(analysis_path.read_text())
    if analysis["status"] != "analyzed" or analysis["source_protocol_sha256"] != audit.file_hash(screen_record):
        raise ValueError("Analise a triagem completa antes de preparar a confirmação")
    selected = analysis["selected_for_confirmation"]
    candidate, arm = selected.split("/")
    source_plan = next((path for path in (root / "short-circuit-preparations").glob("*/plan.json")
                        if protocol_digest(protocol.read_protocol(path.parent / "hardware_screen_protocol.json"))
                        == record["protocol_sha256"]), None)
    if source_plan is None:
        raise ValueError("Plano autenticado da triagem não encontrado")
    plan = json.loads(source_plan.read_text())
    if plan["protocol_sha256"] != audit.file_hash(source_plan.parent / "hardware_screen_protocol.json"):
        raise ValueError("Protocolo da triagem alterado após a preparação")
    for preview in plan["previews"].values():
        if audit.file_hash(source_plan.parent / preview["qpy_file"]) != preview["qpy_sha256"]:
            raise ValueError("Prévia QPY da triagem ausente ou alterada")
    backend = plan["backend"]
    layout = plan["previews"][candidate]["initial_layout"]
    target = ibm_runtime._service().backend(backend)
    if not target.status().operational or getattr(target.configuration(), "simulator", False):
        raise ValueError("Backend IBM não está operacional para a confirmação")
    cfg = ExperimentConfig.from_dict(config(90001))
    circuit = build_trotter_circuit(cfg, 1.5, CANDIDATES[candidate]["steps"])
    circuit.measure_all()
    compiled = generate_preset_pass_manager(backend=target, optimization_level=3,
                 seed_transpiler=81001, initial_layout=layout).run(circuit)
    two_qubit = sum(count for gate, count in compiled.count_ops().items()
                    if gate in {"cx", "cz", "ecr", "rzz", "rxx", "ryy"})
    if compiled.depth() > 5000 or two_qubit >= 672:
        raise ValueError("Circuito da confirmação excede os limites declarados; nenhum job enviado")
    binary = io.BytesIO()
    qpy.dump(compiled, binary)
    preview_path = source_plan.parent / "confirmation_preview.qpy"
    preview_path.write_bytes(binary.getvalue())
    steps = []
    for seed in range(90001, 90021):
        parent = f"confirm_{candidate}_s{seed}"
        steps.extend([
            {"id": parent, "action": "classical", "request": {
                "config": config(seed), "trajectories": 4096, "substeps": 12}},
            {"id": parent + "_ideal", "action": "quantum", "run_from": parent,
             "request": {"steps": CANDIDATES[candidate]["steps"], "shots": 32, "readout_error": 0.}},
            {"id": parent + "_hardware", "action": "hardware", "run_from": parent,
             "request": {"backend": backend, "interval_index": 1,
                         "steps": CANDIDATES[candidate]["steps"], "shots": 16384,
                         "kind": "c3", "index": 0, "role": "raw",
                         "initial_layout": layout, "max_depth": 5000,
                         "transpiler_seed": 81001, "optimization_level": 3,
                         "gate_twirling": arm == "twirled"}}
        ])
    spec = protocol.ProtocolSpec(name="T11-circuitos-curtos-IBM-confirmacao-v2", steps=steps,
        description=f"Confirmacao independente pos triagem: {selected}; N4 mu3 tau1.5; 20 sementes 90001-90020; 327680 shots. Criterio D e IC95 fixados no design v2.")
    destination = source_plan.parent / "confirmation_protocol.json"
    audit.atomic_json(destination, spec.model_dump(mode="json"))
    prepared = {"status": "prepared_not_submitted", "selected": selected,
                "source_screen_record": str(screen_record),
                "source_screen_analysis_sha256": audit.file_hash(analysis_path),
                "protocol_path": str(destination), "protocol_sha256": audit.file_hash(destination),
                "preview": {"depth": compiled.depth(), "two_qubit_gates": two_qubit,
                            "qpy_file": preview_path.name, "qpy_sha256": audit.file_hash(preview_path)},
                "planned_jobs": 20, "total_shots": 327680, "ibm_jobs_submitted": 0}
    audit.atomic_json(source_plan.parent / "confirmation_plan.json", prepared)
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["define", "preflight", "analyze-local", "prepare-hardware",
                                            "collect-hardware", "prepare-confirmation"])
    parser.add_argument("--check", action="store_true", help="Conferir JSONs versionados sem gravar")
    parser.add_argument("--backend", help="Backend IBM somente em prepare-hardware")
    parser.add_argument("--local-record", type=Path, help="run.json local concluído")
    parser.add_argument("--record", type=Path, help="run.json da triagem ou confirmação IBM")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--max-depth", type=int, default=5000)
    args = parser.parse_args()
    service.store = RunStore(args.output.resolve())
    try:
        if args.command == "define":
            differences = definitions(args.check)
            result = {"status": "different" if differences else "ok", "differences": differences}
        elif args.command == "preflight":
            result = ideal_preflight()
            path = service.store.root / "short_circuit_preflight.json"
            audit.atomic_json(path, result)
            result["record_path"] = str(path)
        elif args.command == "analyze-local":
            if not args.record:
                parser.error("analyze-local exige --record")
            result = analyze_local(args.record, args.output)
        elif args.command == "prepare-hardware":
            if not args.backend or not args.local_record:
                parser.error("prepare-hardware exige --backend e --local-record")
            if definitions(True):
                raise ValueError("Definições v2 divergentes; execute define --check")
            result = prepare_hardware(args.backend, args.local_record, args.output, args.max_depth)
        elif args.command == "collect-hardware":
            if not args.record:
                parser.error("collect-hardware exige --record")
            result = collect_hardware(args.record, args.output)
        else:
            if not args.record:
                parser.error("prepare-confirmation exige --record da triagem")
            result = prepare_confirmation(args.record, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") not in {"different", "failed"} else 1
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Falha: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
