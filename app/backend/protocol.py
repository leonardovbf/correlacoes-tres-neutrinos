"""Protocolos JSON sequenciais, retomada e comparação de reproduções locais."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from . import audit, service
from .schemas import (MitigationRequest, AerRequest, CircuitRequest, ClassicalRequest, IntervalRequest,
                      HardwareRequest, QuantumRequest, StrictModel)


REQUESTS = {"mitigation": MitigationRequest, "classical": ClassicalRequest, "quantum": QuantumRequest,
            "circuit": CircuitRequest, "aer": AerRequest,
            "interval": IntervalRequest, "hardware": HardwareRequest}


class ProtocolStep(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    action: Literal["classical", "quantum", "circuit", "aer", "mitigation", "interval",
                    "convergence", "hardware", "hardware_refresh"]
    run_from: str | None = None
    run_id: str | None = None
    job_id: str | None = None
    request: dict = Field(default_factory=dict)


class ProtocolSpec(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    steps: list[ProtocolStep] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def validate_steps(self):
        seen = set()
        for step in self.steps:
            if step.id in seen:
                raise ValueError(f"Etapa repetida: {step.id}")
            if step.action == "classical":
                if step.run_from or step.run_id:
                    raise ValueError("A etapa classical cria seu próprio experimento")
            elif bool(step.run_from) == bool(step.run_id):
                raise ValueError(f"{step.id}: informe run_from ou run_id")
            if step.run_from and step.run_from not in seen:
                raise ValueError(f"{step.id}: run_from deve apontar para uma etapa anterior")
            if step.action == "hardware_refresh":
                if not step.job_id:
                    raise ValueError("hardware_refresh exige o job_id já existente")
            elif step.job_id:
                raise ValueError("job_id é permitido somente em hardware_refresh")
            if step.action in REQUESTS:
                step.request = REQUESTS[step.action].model_validate(step.request).model_dump(mode="json")
            elif step.request:
                raise ValueError(f"{step.action} não recebe request")
            seen.add(step.id)
        return self


class ProtocolFailed(RuntimeError):
    def __init__(self, message: str, record_path: Path):
        super().__init__(message)
        self.record_path = record_path


def read_protocol(path: Path) -> ProtocolSpec:
    return ProtocolSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _artifact_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Artefato aponta para fora do diretório de resultados")
    return path


def verify_artifacts(root: Path, execution: dict) -> None:
    for artifact in execution.get("artifacts", []):
        path = _artifact_path(root, artifact["path"])
        if not path.is_file() or audit.file_hash(path) != artifact["sha256"]:
            raise ValueError(f"Artefato ausente ou alterado: {artifact['path']}")


def _perform(step: ProtocolStep, run_id: str | None) -> dict:
    if step.action == "classical":
        return service.create_experiment(ClassicalRequest(**step.request))
    if step.action == "convergence":
        return service.run_convergence(run_id)
    if step.action == "hardware_refresh":
        return service.refresh_hardware(run_id, step.job_id)
    function = {"mitigation": service.run_mitigation, "quantum": service.run_quantum, "circuit": service.verify_circuit,
                "aer": service.run_aer, "interval": service.get_interval,
                "hardware": service.submit_hardware}[step.action]
    return function(run_id, REQUESTS[step.action](**step.request))


def run_protocol(spec: ProtocolSpec, *, resume: Path | None = None,
                 allow_hardware: bool = False, allow_environment_drift: bool = False,
                 progress=None, on_record=None, step_validator=None) -> dict:
    root = service.store.root
    normalized = spec.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    started = time.perf_counter()
    if resume is not None:
        path = resume.resolve()
        if path.parent.parent != (root / "protocols").resolve():
            raise ValueError("A retomada deve usar o mesmo diretório --output do protocolo")
        record = json.loads(path.read_text())
        if record["protocol_sha256"] != digest:
            raise ValueError("O protocolo mudou; inicie uma nova coleta")
        if record["status"] == "running":
            if audit.process_alive(record.get("process_id")):
                raise ValueError("O processo do protocolo ainda está ativo")
        differences = audit.environment_differences(record["environment"])
        if differences and not allow_environment_drift:
            raise ValueError("Ambiente diferente; use o snapshot original: " + "; ".join(differences))
        record.setdefault("resumptions", []).append({"utc": audit.utc_now(),
            "environment_differences": differences, "environment": audit.environment()})
    else:
        protocol_id = audit.new_id()
        path = root / "protocols" / protocol_id / "run.json"
        snapshot = audit.environment()
        record = {"schema_version": 1, "protocol_run_id": protocol_id, "name": spec.name,
            "protocol_sha256": digest, "status": "running", "started_utc": audit.utc_now(),
            "finished_utc": None, "environment": snapshot,
            "source_snapshot": audit.archive_environment(root, snapshot), "error": None,
            "steps": [{"id": step.id, "action": step.action, "status": "pending",
                       "attempts": [], "execution_id": None, "run_id": None} for step in spec.steps]}
        audit.atomic_json(path.parent / "protocol.json", normalized)
    record.update(status="running", process_id=os.getpid(), error=None, finished_utc=None)
    audit.atomic_json(path, record)
    if on_record:
        on_record(path)
    runs = {}
    current = None
    previous_execution = None
    try:
        if any(step.action == "hardware" and state["status"] != "completed"
               for step, state in zip(spec.steps, record["steps"], strict=True)) and not allow_hardware:
            raise ValueError("O protocolo envia jobs IBM. Use --allow-hardware somente para autorizar novos envios")
        for step, state in zip(spec.steps, record["steps"], strict=True):
            current = state
            if state["status"] == "completed":
                execution = audit.load_execution(root, state["execution_id"])
                verify_artifacts(root, execution)
                runs[step.id] = state["run_id"]
                continue
            if resume and step.action == "hardware" and state.get("execution_id"):
                raise ValueError("Envio IBM anterior não foi concluído localmente; confira o job na IBM antes de criar outro protocolo")
            if state.get("execution_id"):
                previous = audit.load_execution(root, state["execution_id"])
                if state["attempts"] and state["attempts"][-1]["status"] == "running":
                    state["attempts"][-1]["status"] = previous["status"]
            differences = audit.environment_differences(record["environment"])
            if differences and not allow_environment_drift:
                raise ValueError("O ambiente mudou durante o protocolo: " + "; ".join(differences))
            state["environment_differences"] = differences
            run_id = runs[step.run_from] if step.run_from else step.run_id
            state.update(status="running", started_utc=audit.utc_now(), error=None)
            audit.atomic_json(path, record)
            if progress:
                progress(f"{step.id}: {step.action}")
            previous_execution = audit.last_execution_id()

            def on_started(execution_id):
                state["execution_id"] = execution_id
                state["attempts"].append({"execution_id": execution_id, "status": "running"})
                audit.atomic_json(path, record)

            with audit.protocol_step(record["protocol_run_id"], step.id, on_started):
                result = _perform(step, run_id)
            if step_validator:
                step_validator(root, step, result)
            execution_id = audit.last_execution_id()
            run_id = result.get("run_id", run_id)
            state.update(status="completed", execution_id=execution_id, run_id=run_id,
                         finished_utc=audit.utc_now())
            state["attempts"][-1]["status"] = "completed"
            runs[step.id] = run_id
            audit.atomic_json(path, record)
        record["status"] = "completed"
    except BaseException as exc:
        execution_id = audit.last_execution_id()
        if current is not None and current["status"] == "running":
            current.update(status="failed", error=audit.safe_error(exc), finished_utc=audit.utc_now())
            if execution_id and execution_id != previous_execution:
                current["execution_id"] = execution_id
                if current["attempts"] and current["attempts"][-1]["execution_id"] == execution_id:
                    current["attempts"][-1]["status"] = "failed"
                else:
                    current["attempts"].append({"execution_id": execution_id, "status": "failed"})
        record["status"] = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
        record["error"] = audit.safe_error(exc)
        raise ProtocolFailed(record["error"]["message"], path) from exc
    finally:
        record["finished_utc"] = audit.utc_now()
        record["last_attempt_duration_ms"] = round((time.perf_counter() - started) * 1000)
        audit.atomic_json(path, record)
    return {**record, "record_path": str(path.resolve())}


def _compare_json(left, right, atol: float, rtol: float) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_compare_json(left[key], right[key], atol, rtol) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_compare_json(a, b, atol, rtol) for a, b in zip(left, right))
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, abs_tol=atol, rel_tol=rtol)
    return left == right


def _compare_execution(old_root: Path, old: dict, new_root: Path, new: dict,
                       atol: float, rtol: float) -> dict:
    if old["action"] in {"hardware", "hardware_refresh"} or old["status"] != "completed":
        return {"checked": False, "reason": "Medição remota ou tentativa original sem resultado completo"}
    prefixes = {"classical": ("exact_", "mean_", "psa_"), "quantum": ("ideal_", "measured_")}
    checks = []
    if old["action"] in {*prefixes, "aer", "mitigation"}:
        def arrays_path(root, record):
            artifact = next(item for item in record["artifacts"] if item["path"].endswith("/moments.npz"))
            return _artifact_path(root, artifact["path"])
        with np.load(arrays_path(old_root, old), allow_pickle=False) as a, np.load(arrays_path(new_root, new), allow_pickle=False) as b:
            if old["action"] == "mitigation":
                previous = json.loads(_artifact_path(old_root, old["result"]["path"]).read_text())
                repeated = json.loads(_artifact_path(new_root, new["result"]["path"]).read_text())
                keys = [(previous["counts_keys"][label], repeated["counts_keys"][label])
                        for label in ("raw", "signal", "zero", "one")]
                previous.pop("counts_keys")
                repeated.pop("counts_keys")
                checks.append({"artifact": "mitigation_estimate_and_metadata",
                               "pass": _compare_json(previous, repeated, atol, rtol)})
            else:
                names = ([key for key in a.files if key.startswith(prefixes[old["action"]])]
                         if old["action"] in prefixes else ["aer_counts"])
                keys = [(key, key) for key in names]
            for key, repeated_key in keys:
                left, right = a[key], b[repeated_key]
                equal = left.shape == right.shape and (
                    np.array_equal(left, right) if left.dtype.kind in "biu" else np.allclose(left, right, atol=atol, rtol=rtol))
                checks.append({"artifact": key, "pass": bool(equal),
                    "max_absolute_difference": float(np.max(np.abs(left - right))) if left.size and left.shape == right.shape else None})
    else:
        left = json.loads(_artifact_path(old_root, old["result"]["path"]).read_text())
        right = json.loads(_artifact_path(new_root, new["result"]["path"]).read_text())
        checks.append({"artifact": "result.json", "pass": _compare_json(left, right, atol, rtol)})
    return {"checked": True, "pass": bool(checks) and all(item["pass"] for item in checks),
            "atol": atol, "rtol": rtol, "checks": checks}


def replay_execution(path: Path, *, allow_environment_drift: bool = False,
                     allow_hardware: bool = False, atol: float = 1e-10,
                     rtol: float = 1e-8, progress=None) -> dict:
    if not all(math.isfinite(value) and value >= 0 for value in (atol, rtol)):
        raise ValueError("Tolerâncias devem ser finitas e não negativas")
    path = path.resolve()
    old_root = path.parents[2]
    old = json.loads(path.read_text())
    recipe = path.parent / "protocol.json"
    if audit.file_hash(recipe) != old["replay_protocol_sha256"]:
        raise ValueError("A receita foi alterada desde a execução original")
    verify_artifacts(old_root, old)
    differences = audit.environment_differences(old["environment"])
    if differences and not allow_environment_drift:
        raise ValueError("Ambiente diferente; use o snapshot original: " + "; ".join(differences))
    result = run_protocol(read_protocol(recipe), allow_hardware=allow_hardware,
                          allow_environment_drift=allow_environment_drift, progress=progress)
    new = audit.load_execution(service.store.root, result["steps"][-1]["execution_id"])
    comparison = _compare_execution(old_root, old, service.store.root, new, atol, rtol)
    result.update(reproduces_execution=old["execution_id"], environment_differences=differences,
                  comparison=comparison)
    record_path = Path(result["record_path"])
    audit.atomic_json(record_path.parent / "comparison.json", comparison)
    if comparison.get("checked") and not comparison["pass"]:
        result["status"] = "verification_failed"
        audit.atomic_json(record_path, result)
        raise ProtocolFailed("A reprodução calculou resultados diferentes; consulte comparison.json", record_path)
    audit.atomic_json(record_path, result)
    return result
