"""Orquestra o motor científico e prepara dados comuns para a interface."""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np

from neutrinos import (ExperimentConfig, bootstrap_counts_interval,
                       bootstrap_interval, classical_exact, mean_field,
                       observable_from_counts, phase_space, quantum_trotter,
                       summarize_errors)
from neutrinos.sim import MomentSeries, _symmetric_trotter_step, initial_state

from . import ibm_runtime
from .audit import recorded
from .schemas import AerRequest, ClassicalRequest, CircuitRequest, HardwareRequest, IntervalRequest, QuantumRequest
from .storage import ROOT, RunStore


store = RunStore()
Progress = Callable[[dict], None]
BOOTSTRAP_SEED = 1234
BOOTSTRAP_REPETITIONS = 200


def _trace(progress: Progress | None, previous: list[dict] | None = None):
    events = list(previous or [])
    started = time.perf_counter()
    offset_ms = events[-1]["elapsed_ms"] if events else 0

    def emit(stage: str, status: str, message: str, source: str, **details) -> None:
        event = {"order": len(events) + 1, "elapsed_ms": offset_ms + round((time.perf_counter() - started) * 1000),
                 "stage": stage, "status": status, "message": message, "source": source}
        if details:
            event["details"] = details
        events.append(event)
        if progress is not None:
            progress(event)

    return events, emit


def _series_json(series: MomentSeries) -> dict:
    data = {"method": series.method, "diagnostics": series.diagnostics}
    for name in ("m1", "m2", "m3", "pe", "c2", "c3"):
        data[name] = getattr(series, name).tolist()
    if series.bloch is not None:
        data["bloch"] = series.bloch.tolist()
    return data


def _series_arrays(prefix: str, series: MomentSeries) -> dict[str, np.ndarray]:
    arrays = {f"{prefix}_{field}": getattr(series, field)
              for field in ("m1", "m2", "m3", "pe", "c2", "c3")}
    if series.bloch is not None:
        arrays[f"{prefix}_bloch"] = series.bloch
    if series.sample_z is not None:
        arrays[f"{prefix}_sample_z"] = series.sample_z
    if series.raw_counts is not None:
        arrays[f"{prefix}_counts"] = series.raw_counts
    return arrays


def _metrics(reference: MomentSeries, other: MomentSeries) -> dict:
    return summarize_errors(reference, other)


def _quality(exact: MomentSeries, mean: MomentSeries, psa: MomentSeries,
             trajectories: int, seed: int) -> dict:
    initial_error = max(
        float(np.max(np.abs(getattr(exact, key)[0] - getattr(psa, key)[0])))
        for key in ("m1", "m2", "m3") if getattr(exact, key).shape[1]
    )
    controls = [
        {"name": "Norma da referência exata", "value": exact.diagnostics["max_norm_error"], "limit": 1e-8},
        {"name": "Comprimento dos spins · campo médio", "value": mean.diagnostics["max_spin_length_error"], "limit": 1e-4},
        {"name": "Momentos Z da PSA em τ=0", "value": initial_error, "limit": 4 / np.sqrt(trajectories)},
    ]
    for control in controls:
        control["pass"] = bool(control["value"] < control["limit"])
    return {"controls": controls, "psa_initial_spin_mean_error_max":
            psa.diagnostics["initial_spin_mean_error_max"], "trajectories": trajectories,
            "seed": seed, "convergence": None}


def _provenance(config: ExperimentConfig, request: ClassicalRequest, quality: dict) -> dict:
    source_files = (ROOT / "pyproject.toml", ROOT / "requirements-research.lock",
                    ROOT / "configs" / "estudos" / "artigo_v1.json", ROOT / "PROTOCOLO_EXPERIMENTOS.md",
                    *sorted((ROOT / "scripts").glob("*.py")),
                    *sorted((ROOT / "app" / "backend").glob("*.py")),
                    *sorted((ROOT / "src" / "neutrinos").glob("*.py")))
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source_files if path.is_file()}
    versions = {}
    for name in ("numpy", "scipy", "fastapi", "uvicorn", "qiskit", "qiskit-aer", "qiskit-ibm-runtime"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": commit, "source_sha256": hashes, "dependencies": versions,
            "config_input": asdict(config), "model": config.record(),
            "classical_options": {"trajectories": request.trajectories, "substeps": request.substeps},
            "quantum_options": None, "aer_runs": [], "hardware_runs": [], "quality": quality,
            "scope": "Simulação local; benchmark publicado e teste confirmatório de H1/H2 pendentes"}


@recorded("classical", lambda: store)
def create_experiment(request: ClassicalRequest, progress: Progress | None = None) -> dict:
    trace, emit = _trace(progress)
    emit("config", "running", "Validando partículas, frequências e acoplamentos", "ExperimentConfig")
    try:
        config = ExperimentConfig.from_dict(request.config)
    except (TypeError, OverflowError) as exc:
        raise ValueError(f"Configuração inválida: {exc}") from exc
    emit("config", "done", f"Modelo preparado: {config.n} neutrinos, dimensão {1 << config.n}", "ExperimentConfig",
         model=config.record(), trajectories=request.trajectories, substeps=request.substeps)
    emit("exact", "running", "Construindo H e evoluindo o estado completo", "classical_exact")
    exact = classical_exact(config)
    emit("exact", "done", f"Referência exata calculada em {config.points} tempos", "classical_exact")
    emit("mean", "running", "Integrando vetores de Bloch com RK4", "mean_field")
    mean = mean_field(config, request.substeps)
    emit("mean", "done", "Trajetória de campo médio calculada", "mean_field")
    emit("psa", "running", f"Amostrando {request.trajectories} condições iniciais e trajetórias", "phase_space")
    psa = phase_space(config, request.trajectories, request.substeps)
    emit("psa", "done", "Momentos de um, dois e três corpos calculados", "phase_space")
    emit("quality", "running", "Comparando invariantes e erros", "summarize_errors")
    quality = _quality(exact, mean, psa, request.trajectories, config.seed)
    manifest = _provenance(config, request, quality)
    summary = {"config": config.record(), "times": config.times.tolist(),
               "pairs": config.pair_index.tolist(), "trios": config.trio_index.tolist(),
               "classical": {"exact": _series_json(exact), "mean": _series_json(mean),
                             "psa": _series_json(psa)},
               "metrics": {"mean": _metrics(exact, mean), "psa": _metrics(exact, psa)},
               "quantum": None, "aer": None, "hardware_runs": [], "quality": quality, "trace": trace}
    arrays = {"times": config.times, "pairs": config.pair_index, "trios": config.trio_index}
    for name, series in (("exact", exact), ("mean", mean), ("psa", psa)):
        arrays.update(_series_arrays(name, series))
    emit("quality", "done", "Invariantes e métricas preparados para registro", "summarize_errors")
    emit("persist", "running", "Gravando manifesto e matrizes brutas", "RunStore")
    summary["trace"] = [event for event in trace if event["stage"] != "persist"]
    manifest["trace"] = summary["trace"]
    run_id = store.create(manifest, summary, arrays)
    emit("persist", "done", f"Execução {run_id} registrada em results/", "RunStore")
    return {"run_id": run_id, **summary}


def get_experiment(run_id: str) -> dict:
    _, summary = store.load_metadata(run_id)
    return {"run_id": run_id, **summary}


def _config(manifest: dict) -> ExperimentConfig:
    return ExperimentConfig.from_dict(manifest["config_input"])


@recorded("quantum", lambda: store)
def run_quantum(run_id: str, request: QuantumRequest, progress: Progress | None = None) -> dict:
    with store.lock:
        manifest, summary, arrays = store.load(run_id)
        config = _config(manifest)
        trace, emit = _trace(progress, summary.get("trace"))
        emit("quantum", "running", f"Aplicando Trotter simétrico: {request.steps} passos por intervalo", "quantum_trotter")
        ideal, measured = quantum_trotter(config, request.steps, request.shots, request.readout_error)
        emit("quantum", "done", f"Circuito ideal e {request.shots} medições por tempo calculados", "quantum_trotter")
        emit("compare", "running", "Comparando circuito com a referência exata", "summarize_errors")
        exact = _series_from_arrays(config, arrays, "exact")
        summary["quantum"] = {"ideal": _series_json(ideal), "measured": _series_json(measured),
                              "options": request.model_dump()}
        summary["metrics"].update({"ideal": _metrics(exact, ideal),
                                   "measured": _metrics(exact, measured)})
        arrays.update(_series_arrays("ideal", ideal))
        arrays.update(_series_arrays("measured", measured))
        manifest["quantum_options"] = request.model_dump()
        emit("compare", "done", "Erros quânticos calculados", "summarize_errors")
        emit("persist", "running", "Gravando revisão com contagens de medição", "RunStore")
        summary["trace"] = [event for event in trace if event["stage"] != "persist"]
        manifest["trace"] = summary["trace"]
        store.update(run_id, manifest, summary, arrays)
        emit("persist", "done", "Revisão quântica registrada", "RunStore")
        return {"run_id": run_id, **summary}


@recorded("hardware", lambda: store)
def submit_hardware(run_id: str, request: HardwareRequest, progress: Progress | None = None) -> dict:
    manifest, summary = store.load_metadata(run_id)
    config = _config(manifest)
    if config.n > 8 or request.interval_index >= config.points:
        raise ValueError("Instante ou número de qubits fora do cenário")
    if request.interval_index * request.steps > 16:
        raise ValueError("Hardware limitado a 16 subpassos Trotter por execução")
    if summary.get("quantum") is None or summary["quantum"]["options"]["steps"] != request.steps:
        raise ValueError("Execute primeiro o circuito local com o mesmo número de passos")
    groups = {"pe": [(i,) for i in range(config.n)],
              "c2": [tuple(map(int, pair)) for pair in config.pair_index],
              "c3": [tuple(map(int, trio)) for trio in config.trio_index]}
    if request.index >= len(groups[request.kind]):
        raise ValueError("Índice de observável fora do cenário")

    trace, emit = _trace(progress, summary.get("trace"))
    emit("ibm", "running", "Transpilando e enviando um instante ao IBM Quantum", "build_trotter_circuit")
    submitted = ibm_runtime.submit(config, request)
    encoded_circuit = submitted.pop("circuit_qpy_base64", None)
    emit("ibm", "done", f"Job {submitted['job_id']} enviado a {submitted['backend']}", "build_trotter_circuit",
         job_id=submitted["job_id"], backend=submitted["backend"])
    entry = {**submitted, **request.model_dump(),
             "tau": float(config.times[request.interval_index]),
             "indices": groups[request.kind][request.index],
             "status": "QUEUED", "estimate": None, "lower": None, "upper": None,
             "references": {
                 "exact": summary["classical"]["exact"][request.kind][request.interval_index][request.index],
                 "ideal": summary["quantum"]["ideal"][request.kind][request.interval_index][request.index],
             }}
    with store.lock:
        manifest, summary, arrays = store.load(run_id)
        if encoded_circuit is not None:
            circuit_bytes = base64.b64decode(encoded_circuit, validate=True)
            circuit_key = f"ibm_{len(summary.get('hardware_runs', [])) + 1:04d}_circuit_qpy"
            arrays[circuit_key] = np.frombuffer(circuit_bytes, dtype=np.uint8)
            entry["circuit_artifact"] = {"format": "qpy", "array_key": circuit_key,
                                         "sha256": submitted["circuit_sha256"]}
        summary.setdefault("hardware_runs", []).append(entry)
        manifest.setdefault("hardware_runs", []).append({key: value for key, value in entry.items()
                                                         if key not in {"estimate", "lower", "upper", "references"}})
        summary["trace"] = [event for event in trace if event["stage"] != "persist"]
        manifest["trace"] = summary["trace"]
        store.update(run_id, manifest, summary, arrays)
    return {"run_id": run_id, **summary}


@recorded("hardware_refresh", lambda: store)
def refresh_hardware(run_id: str, job_id: str, progress: Progress | None = None) -> dict:
    _, emit = _trace(progress)
    emit("ibm_status", "running", "Consultando job IBM já existente", "fetch")
    manifest, summary = store.load_metadata(run_id)
    existing = next((entry for entry in summary.get("hardware_runs", [])
                     if entry["job_id"] == job_id), None)
    if existing is None:
        raise ValueError("Job IBM não pertence a este experimento")
    if existing["status"] in {"DONE", "ERROR", "CANCELLED"}:
        emit("ibm_status", "done", f"Resultado já registrado: {existing['status']}", "fetch")
        return existing

    config = _config(manifest)
    state, counts = ibm_runtime.fetch(job_id, config.n)
    emit("ibm_status", "done", f"Estado devolvido pela IBM: {state}", "fetch")
    checked_utc = datetime.now(timezone.utc).isoformat()
    if state == existing["status"]:
        return {**existing, "checked_utc": checked_utc}
    with store.lock:
        manifest, summary, arrays = store.load(run_id)
        entry = next(item for item in summary["hardware_runs"] if item["job_id"] == job_id)
        if entry["status"] in {"DONE", "ERROR", "CANCELLED"}:
            return entry
        entry["status"] = state
        entry["checked_utc"] = checked_utc
        if counts is not None:
            emit("observables", "running", "Calculando observável e incerteza das contagens IBM", "observable_from_counts")
            if int(counts.sum()) != entry["shots"]:
                raise ValueError("Contagens retornadas pela IBM não correspondem às medições pedidas")
            indices = tuple(entry["indices"])
            entry["estimate"] = observable_from_counts(counts, entry["kind"], indices)
            lower, upper = bootstrap_counts_interval(counts, entry["kind"], indices,
                                                     repetitions=BOOTSTRAP_REPETITIONS, seed=BOOTSTRAP_SEED)
            entry["lower"], entry["upper"] = lower, upper
            entry["uncertainty"] = {"method": "multinomial-percentile", "confidence": .95,
                                     "repetitions": BOOTSTRAP_REPETITIONS, "seed": BOOTSTRAP_SEED}
            count_key = f"ibm_{summary['hardware_runs'].index(entry) + 1:04d}_counts"
            arrays[count_key] = counts
            entry["counts_key"] = count_key
            emit("observables", "done", "Contagens e estimativa IBM preparadas", "observable_from_counts")
        for item in manifest.get("hardware_runs", []):
            if item["job_id"] == job_id:
                item["status"] = state
                if "counts_key" in entry:
                    item["counts_key"] = entry["counts_key"]
                break
        emit("persist", "running", "Salvando revisão do resultado IBM", "RunStore")
        store.update(run_id, manifest, summary, arrays)
        emit("persist", "done", "Resultado IBM salvo", "RunStore")
        return entry


def _series_from_arrays(config: ExperimentConfig, arrays: dict[str, np.ndarray],
                        prefix: str) -> MomentSeries:
    return MomentSeries(config.times, arrays[f"{prefix}_m1"], arrays[f"{prefix}_m2"],
                        arrays[f"{prefix}_m3"], config.pair_index, config.trio_index,
                        prefix, {}, sample_z=arrays.get(f"{prefix}_sample_z"),
                        raw_counts=arrays.get(f"{prefix}_counts"))


@recorded("interval", lambda: store)
def get_interval(run_id: str, request: IntervalRequest, progress: Progress | None = None) -> dict:
    _, emit = _trace(progress)
    emit("bootstrap", "running", "Reamostrando trajetórias ou contagens completas", "bootstrap_interval")
    manifest, _, arrays = store.load(run_id)
    config = _config(manifest)
    indices = {"pe": config.n, "c2": len(config.pair_index), "c3": len(config.trio_index)}
    if request.index >= indices[request.kind]:
        raise ValueError("Índice de observável fora do cenário")
    if request.method == "measured" and "measured_counts" not in arrays:
        raise ValueError("Execute o circuito antes de pedir o intervalo das medições")
    series = _series_from_arrays(config, arrays, request.method)
    lower, upper = bootstrap_interval(series, request.kind, request.index,
                                     repetitions=request.repetitions, seed=request.seed)
    emit("bootstrap", "done", "Intervalo de confiança calculado", "bootstrap_interval")
    return {"lower": lower.tolist(), "upper": upper.tolist(), "confidence": 0.95,
            "scope": "pontual; sem correção para múltiplas comparações"}


def _qiskit_worker(config: ExperimentConfig, action: str, steps: int, **kwargs) -> dict:
    payload = {"action": action, "config": asdict(config), "steps_per_interval": steps, **kwargs}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run([sys.executable, "-m", "neutrinos.aer_worker"],
                            input=json.dumps(payload), text=True, capture_output=True,
                            cwd=ROOT, env=env, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(f"Qiskit terminou com código {result.returncode}: {result.stderr[-800:]}")
    return json.loads(result.stdout)


@recorded("circuit", lambda: store)
def verify_circuit(run_id: str, request: CircuitRequest, progress: Progress | None = None) -> dict:
    _, emit = _trace(progress)
    emit("qiskit", "running", "Executando circuito independente no Qiskit", "first_interval_probabilities")
    manifest, _ = store.load_metadata(run_id)
    config = _config(manifest)
    if config.n > 8:
        raise ValueError("Circuito interativo limitado a 8 neutrinos")
    result = _qiskit_worker(config, "first_interval", request.steps)
    state = initial_state(config)
    dt = float(config.times[1] - config.times[0]) / request.steps
    for _ in range(request.steps):
        _symmetric_trotter_step(state, config, dt)
    result["max_probability_difference"] = float(np.max(
        np.abs(np.asarray(result.pop("probabilities")) - np.abs(state) ** 2)))
    emit("qiskit", "done", "Probabilidades Qiskit comparadas ao emulador", "first_interval_probabilities")
    return result


@recorded("aer", lambda: store)
def run_aer(run_id: str, request: AerRequest, progress: Progress | None = None) -> dict:
    _, emit = _trace(progress)
    with store.lock:
        manifest, summary, arrays = store.load(run_id)
        config = _config(manifest)
        if config.n > 8:
            raise ValueError("Aer interativo limitado a 8 neutrinos")
        if request.interval_index >= config.points or request.interval_index * request.steps > 120:
            raise ValueError("Instante ou profundidade fora do limite de 120 passos")
        group = {"pe": config.n, "c2": len(config.pair_index), "c3": len(config.trio_index)}
        if request.index >= group[request.kind]:
            raise ValueError("Índice de observável fora do cenário")
        indices = {"pe": [(i,) for i in range(config.n)],
                   "c2": [tuple(int(i) for i in x) for x in config.pair_index],
                   "c3": [tuple(int(i) for i in x) for x in config.trio_index]}[request.kind][request.index]
        emit("aer", "running", "Transpilando e simulando portas e leitura com ruído", "simulate_gate_noise")
        worker = _qiskit_worker(config, "gate_noise", request.steps,
                                interval_index=request.interval_index, shots=request.shots,
                                single_qubit_error=request.single_qubit_error,
                                two_qubit_error=request.two_qubit_error,
                                readout_error=request.readout_error)
        counts = np.asarray(worker["counts"], dtype=np.int64)
        emit("aer", "done", "Contagens Aer recebidas", "simulate_gate_noise")
        emit("observables", "running", "Calculando observável e bootstrap conjunto", "observable_from_counts")
        estimate = observable_from_counts(counts, request.kind, indices)
        lower, upper = bootstrap_counts_interval(counts, request.kind, indices,
                                                 repetitions=BOOTSTRAP_REPETITIONS, seed=BOOTSTRAP_SEED)
        worker["metadata"]["uncertainty"] = {"method": "multinomial-percentile", "confidence": .95,
                                               "repetitions": BOOTSTRAP_REPETITIONS, "seed": BOOTSTRAP_SEED}
        references = {name: summary["classical"][name][request.kind][request.interval_index][request.index]
                      for name in ("exact", "psa")}
        if summary["quantum"] is not None and summary["quantum"]["options"]["steps"] == request.steps:
            references["ideal"] = summary["quantum"]["ideal"][request.kind][request.interval_index][request.index]
        result = {"kind": request.kind, "index": request.index, "indices": indices,
                  "estimate": estimate, "lower": lower, "upper": upper,
                  "references": references, "metadata": worker["metadata"]}
        summary["aer"] = result
        count_key = f"aer_{len(manifest['aer_runs']) + 1:04d}_counts"
        result["counts_key"] = count_key
        arrays["aer_counts"] = counts
        arrays[count_key] = counts
        manifest["aer_runs"].append({**request.model_dump(), "metadata": worker["metadata"],
                                     "counts_key": count_key})
        emit("observables", "done", "Estimativa e intervalo calculados", "observable_from_counts")
        emit("persist", "running", "Salvando contagens Aer com identificador próprio", "RunStore")
        store.update(run_id, manifest, summary, arrays)
        emit("persist", "done", "Resultado Aer salvo", "RunStore")
        return result


@recorded("convergence", lambda: store)
def run_convergence(run_id: str, progress: Progress | None = None) -> dict:
    _, emit = _trace(progress)
    with store.lock:
        manifest, summary, arrays = store.load(run_id)
        config = _config(manifest)
        options = manifest["classical_options"]
        trajectories, substeps = options["trajectories"], options["substeps"]
        base_mean = _series_from_arrays(config, arrays, "mean")
        base_psa = _series_from_arrays(config, arrays, "psa")
        emit("integration", "running", "Refinando subpassos de campo médio e PSA", "mean_field")
        refined_mean = mean_field(config, substeps * 2)
        refined_psa = phase_space(config, trajectories, substeps * 2)
        emit("integration", "done", "Integração refinada calculada", "phase_space")
        emit("sampling", "running", "Comparando trajetórias adicionais e semente independente", "phase_space")
        more_psa = phase_space(config, min(trajectories * 2, 4096), substeps)
        independent = phase_space(ExperimentConfig.from_dict(
            {**manifest["config_input"], "seed": config.seed + 1}), trajectories, substeps)
        emit("sampling", "done", "Amostragem comparada", "phase_space")

        def gap(a: MomentSeries, b: MomentSeries) -> float:
            return float(np.sqrt(np.mean((a.c3 - b.c3) ** 2))) if a.c3.size else 0.0

        result = {"mean_substeps_x2": gap(base_mean, refined_mean),
                  "psa_substeps_x2": gap(base_psa, refined_psa),
                  "psa_trajectories_x2": gap(base_psa, more_psa),
                  "psa_independent_seed": gap(base_psa, independent)}
        summary["quality"]["convergence"] = result
        manifest["quality"] = summary["quality"]
        emit("persist", "running", "Salvando diagnóstico de convergência", "RunStore")
        store.update(run_id, manifest, summary, arrays)
        emit("persist", "done", "Diagnóstico de convergência salvo", "RunStore")
        return result


def example_scenario() -> dict:
    return json.loads((ROOT / "configs" / "cenario_exemplo.json").read_text(encoding="utf-8"))
