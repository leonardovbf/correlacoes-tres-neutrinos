"""Registro durável de cada tentativa e receita para repetir cálculos locais."""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
IDENTIFIER = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")
_lock = threading.RLock()
_last_execution = contextvars.ContextVar("last_execution", default=None)
_protocol_context = contextvars.ContextVar("protocol_context", default=None)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:12]}"


def atomic_json(path: Path, value) -> None:
    """Troca atômica: o leitor encontra o JSON anterior ou o novo completo."""
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        descriptor, temporary = tempfile.mkstemp(prefix=".json-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_error(exc: BaseException) -> dict:
    message = str(exc)
    # Nunca copiar credenciais do ambiente para erros arquivados.
    for name in ("IBM_QUANTUM_API_KEY", "IBM_QUANTUM_TOKEN"):
        secret = os.environ.get(name, "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return {"type": type(exc).__name__, "message": message}


def safe_inputs(value):
    if isinstance(value, dict):
        return {key: "[REDACTED]" if any(word in key.lower() for word in ("api_key", "token", "password", "secret"))
                else safe_inputs(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_inputs(item) for item in value]
    if isinstance(value, str):
        for name in ("IBM_QUANTUM_API_KEY", "IBM_QUANTUM_TOKEN"):
            secret = os.environ.get(name, "")
            if secret:
                value = value.replace(secret, "[REDACTED]")
    return value


def process_alive(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def protocol_step(protocol_run_id: str, step_id: str, on_started):
    token = _protocol_context.set({"protocol_run_id": protocol_run_id,
                                  "step_id": step_id, "on_started": on_started})
    try:
        yield
    finally:
        _protocol_context.reset(token)


def environment() -> dict:
    sources = [ROOT / "pyproject.toml", ROOT / "requirements-research.lock",
               ROOT / "configs" / "estudos" / "artigo_v1.json", ROOT / "PROTOCOLO_EXPERIMENTOS.md",
               *sorted((ROOT / "scripts").glob("*.py")), ROOT / "app" / "__init__.py",
               *sorted((ROOT / "app" / "backend").glob("*.py")),
               *sorted((ROOT / "src" / "neutrinos").glob("*.py"))]
    hashes = {str(path.relative_to(ROOT)): file_hash(path) for path in sources if path.is_file()}
    packages = {"numpy", "scipy", "fastapi", "uvicorn", "python-dotenv", "httpx",
                "qiskit", "qiskit-aer", "qiskit-ibm-runtime"}
    lockfile = ROOT / "requirements-research.lock"
    if lockfile.exists():
        packages.update(line.split("==")[0] for line in lockfile.read_text().splitlines()
                        if "==" in line and not line.startswith("#"))
    dependencies = {}
    for name in sorted(packages):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT,
                                             text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    identity = {"source_sha256": hashes, "dependencies": dependencies,
                "python": platform.python_version()}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {**identity, "fingerprint": fingerprint, "git_commit": commit,
            "git_dirty": dirty, "platform": platform.platform(),
            "machine": platform.machine(), "python_implementation": platform.python_implementation()}


def archive_environment(root: Path, snapshot: dict) -> str:
    """Arquiva uma única cópia dos fontes científicos, inclusive alterações locais."""
    destination = root / "_sources" / snapshot["fingerprint"]
    with _lock:
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=".source-", dir=destination.parent))
            try:
                for name, expected in snapshot["source_sha256"].items():
                    target = stage / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                    if file_hash(target) != expected:
                        raise RuntimeError("O código mudou durante a captura; repita a execução")
                atomic_json(stage / "environment.json", snapshot)
                (stage / "requirements.txt").write_text("".join(
                    f"{name}=={version}\n" for name, version in snapshot["dependencies"].items()
                    if version is not None), encoding="utf-8")
                try:
                    os.rename(stage, destination)
                except FileExistsError:
                    pass
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
    return str(destination.relative_to(root))


def environment_differences(saved: dict) -> list[str]:
    current = environment()
    differences = []
    if saved.get("python") != current["python"]:
        differences.append("Versão do Python diferente")
    for name, expected in saved.get("dependencies", {}).items():
        if current["dependencies"].get(name) != expected:
            differences.append(f"Dependência diferente: {name}")
    for name, expected in saved.get("source_sha256", {}).items():
        if current["source_sha256"].get(name) != expected:
            differences.append(f"Fonte diferente: {name}")
    return differences


def load_execution(root: Path, execution_id: str) -> dict:
    if not IDENTIFIER.fullmatch(execution_id):
        raise KeyError(execution_id)
    try:
        path = root / "executions" / execution_id / "execution.json"
        record = json.loads(path.read_text())
    except FileNotFoundError:
        raise KeyError(execution_id) from None
    if record["status"] == "running" and not process_alive(record.get("process_id")):
        record.update(status="interrupted", finished_utc=utc_now(),
                      error={"type": "ProcessInterrupted", "message": "O processo terminou antes de concluir a tentativa"})
        record["steps"].append({"order": len(record["steps"]) + 1, "timestamp_utc": utc_now(),
                               "stage": "execution", "status": "failed", "message": record["error"]["message"]})
        atomic_json(path, record)
    return record


def execution_history(root: Path, run_id: str) -> list[dict]:
    path = root / run_id / "executions.json"
    return json.loads(path.read_text()) if path.exists() else []


def last_execution_id() -> str | None:
    return _last_execution.get()


def _revision(store, run_id: str | None) -> str | None:
    if not run_id:
        return None
    try:
        store.load_metadata(run_id)  # valida o identificador antes de construir caminhos
        return (store.root / run_id / "current").read_text().strip()
    except (KeyError, FileNotFoundError):
        return None


def _recipe(action: str, inputs: dict, manifest: dict | None) -> dict:
    steps = []
    if action == "classical":
        steps.append({"id": "classical", "action": action, "request": inputs["request"]})
    elif action == "hardware_refresh":
        steps.append({"id": "target", "action": action, "run_id": inputs["run_id"],
                      "job_id": inputs["job_id"]})
    elif manifest is not None:
        steps.append({"id": "classical", "action": "classical", "request": {
            "config": manifest["config_input"], **manifest["classical_options"]}})
        if manifest.get("quantum_options") and action != "quantum":
            steps.append({"id": "quantum", "action": "quantum", "run_from": "classical",
                          "request": manifest["quantum_options"]})
        target = {"id": "target", "action": action, "run_from": "classical"}
        if "request" in inputs:
            target["request"] = inputs["request"]
        steps.append(target)
    else:
        target = {"id": "target", "action": action, "run_id": inputs.get("run_id")}
        if "request" in inputs:
            target["request"] = inputs["request"]
        steps.append(target)
    return {"schema_version": 1, "name": f"replay-{action}",
            "description": "Receita da tentativa; usa novas execuções e preserva as originais.",
            "steps": steps}


def recorded(action: str, store_provider):
    """Registra entrada, eventos e falhas mesmo antes de existir um run_id."""
    def decorate(function):
        signature = inspect.signature(function)

        @wraps(function)
        def wrapped(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            inputs = {key: value.model_dump(mode="json") if hasattr(value, "model_dump") else value
                      for key, value in bound.arguments.items() if key != "progress"}
            inputs = safe_inputs(inputs)
            store = store_provider()
            execution_id = new_id()
            directory = store.root / "executions" / execution_id
            snapshot = environment()
            snapshot_path = archive_environment(store.root, snapshot)
            started = time.perf_counter()
            run_id = inputs.get("run_id")
            before = _revision(store, run_id)
            manifest = store.load_metadata(run_id)[0] if before else None
            record = {"schema_version": 1, "execution_id": execution_id, "action": action,
                      "status": "running", "started_utc": utc_now(), "finished_utc": None,
                      "duration_ms": None, "process_id": os.getpid(), "inputs": inputs,
                      "run_id": run_id, "revision_before": before, "revision_after": None,
                      "environment": snapshot, "source_snapshot": snapshot_path,
                      "steps": [], "result": None, "artifacts": [], "error": None,
                      "replay_protocol": "protocol.json"}
            context = _protocol_context.get()
            record["protocol"] = {key: context[key] for key in ("protocol_run_id", "step_id")} if context else None
            atomic_json(directory / "protocol.json", _recipe(action, inputs, manifest))
            record["replay_protocol_sha256"] = file_hash(directory / "protocol.json")

            def event(stage: str, status: str, message: str, source: str = "", **extra):
                record["steps"].append({"order": len(record["steps"]) + 1,
                    "timestamp_utc": utc_now(), "elapsed_ms": round((time.perf_counter() - started) * 1000),
                    "stage": stage, "status": status, "message": message, "source": source, **extra})
                atomic_json(directory / "execution.json", record)

            original_progress = bound.arguments.get("progress")

            def report(value: dict):
                event(value["stage"], value["status"], value["message"], value.get("source", ""),
                      engine_elapsed_ms=value.get("elapsed_ms"), details=value.get("details"))
                if original_progress is not None:
                    original_progress({**value, "execution_id": execution_id})

            if "progress" in signature.parameters:
                bound.arguments["progress"] = report
            event("execution", "running", "Tentativa iniciada")
            try:
                if context:
                    context["on_started"](execution_id)
                result = function(*bound.args, **bound.kwargs)
                if isinstance(result, dict):
                    run_id = result.get("run_id", run_id)
                after = _revision(store, run_id)
                record.update(run_id=run_id, revision_after=after)
                if after:
                    revision = store.root / run_id / "versions" / after
                    index_path = revision / "artifacts.json"
                    index = json.loads(index_path.read_text())["files"] if index_path.exists() else {}
                    for name in ("manifest.json", "summary.json", "moments.npz"):
                        path = revision / name
                        record["artifacts"].append({"path": str(path.relative_to(store.root)),
                            **(index.get(name) or {"sha256": file_hash(path), "bytes": path.stat().st_size})})
                if action in {"classical", "quantum", "hardware"} and after:
                    record["result"] = {"path": f"{run_id}/versions/{after}/summary.json"}
                else:
                    atomic_json(directory / "result.json", result)
                    result_path = directory / "result.json"
                    record["result"] = {"path": str(result_path.relative_to(store.root))}
                    record["artifacts"].append({"path": str(result_path.relative_to(store.root)),
                        "sha256": file_hash(result_path), "bytes": result_path.stat().st_size})
                record["status"] = "completed"
                event("execution", "done", "Tentativa concluída")
                return result
            except BaseException as exc:
                exc.execution_id = execution_id
                record["status"] = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
                record["error"] = safe_error(exc)
                event("execution", "failed", record["error"]["message"])
                raise
            finally:
                record["finished_utc"] = utc_now()
                record["duration_ms"] = round((time.perf_counter() - started) * 1000)
                atomic_json(directory / "execution.json", record)
                _last_execution.set(execution_id)
                if run_id and (store.root / run_id).is_dir():
                    with _lock:
                        history = execution_history(store.root, run_id)
                        history.append({key: record[key] for key in (
                            "execution_id", "action", "status", "started_utc", "finished_utc",
                            "revision_before", "revision_after")})
                        atomic_json(store.root / run_id / "executions.json", history)
        return wrapped
    return decorate
