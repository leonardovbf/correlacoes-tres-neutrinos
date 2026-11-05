"""Execuções em segundo plano com eventos reais do motor científico."""

from __future__ import annotations

import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from . import service
from .audit import atomic_json, last_execution_id, load_execution, process_alive, safe_error, safe_inputs
from .schemas import ClassicalRequest, HardwareRequest, QuantumRequest


class JobManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="neutrino-job")
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}

    def start(self, kind: str, operation: Callable[[Callable[[dict], None]], dict],
              inputs: dict | None = None, run_id: str | None = None) -> dict:
        job_id = uuid4().hex[:16]
        root = service.store.root
        path = root / "jobs" / f"{job_id}.json"
        job = {"job_id": job_id, "kind": kind, "status": "queued", "events": [],
               "run_id": run_id, "error": None, "inputs": safe_inputs(inputs or {}),
               "execution_id": None, "process_id": os.getpid(),
               "created_utc": datetime.now(timezone.utc).isoformat()}
        with self.lock:
            self.jobs[job_id] = job
            atomic_json(path, job)
            if len(self.jobs) > 100:
                finished = [key for key, value in self.jobs.items()
                            if value["status"] in ("completed", "failed") and key != job_id]
                for key in finished[:len(self.jobs) - 100]:
                    self.jobs.pop(key, None)

        def report(event: dict) -> None:
            with self.lock:
                job["events"].append(event)
                job["execution_id"] = event.get("execution_id", job["execution_id"])
                atomic_json(path, job)

        def run() -> None:
            with self.lock:
                job["status"] = "running"
                atomic_json(path, job)
            try:
                result = operation(report)
                with self.lock:
                    job["run_id"] = result["run_id"]
                    job["status"] = "completed"
                    job["execution_id"] = last_execution_id()
                    job["finished_utc"] = datetime.now(timezone.utc).isoformat()
                    atomic_json(path, job)
            except Exception as exc:
                with self.lock:
                    job["error"] = safe_error(exc)["message"]
                    job["status"] = "failed"
                    job["execution_id"] = last_execution_id()
                    job["finished_utc"] = datetime.now(timezone.utc).isoformat()
                    atomic_json(path, job)

        self.executor.submit(run)
        return self.get(job_id)

    def get(self, job_id: str) -> dict:
        with self.lock:
            if job_id not in self.jobs:
                if not re.fullmatch(r"[0-9a-f]{16}", job_id):
                    raise KeyError(job_id)
                path = service.store.root / "jobs" / f"{job_id}.json"
                try:
                    job = json.loads(path.read_text())
                except FileNotFoundError:
                    raise KeyError(job_id) from None
                if job["status"] in {"queued", "running"}:
                    if not process_alive(job.get("process_id")):
                        job.update(status="failed", error="Execução interrompida pelo encerramento do processo; consulte o registro JSON",
                                   finished_utc=datetime.now(timezone.utc).isoformat())
                        atomic_json(path, job)
                        if job.get("execution_id"):
                            load_execution(service.store.root, job["execution_id"])
                return job
            job = self.jobs[job_id]
            return {**job, "events": list(job["events"])}


manager = JobManager()


def start_classical(request: ClassicalRequest) -> dict:
    return manager.start("classical", lambda report: service.create_experiment(request, progress=report),
                         inputs=request.model_dump())


def start_quantum(run_id: str, request: QuantumRequest) -> dict:
    # Falhas de identificador retornam imediatamente ao cliente.
    service.store.load_metadata(run_id)
    return manager.start("quantum", lambda report: service.run_quantum(run_id, request, progress=report),
                         inputs=request.model_dump(), run_id=run_id)


def start_hardware(run_id: str, request: HardwareRequest) -> dict:
    service.store.load_metadata(run_id)
    return manager.start("hardware", lambda report: service.submit_hardware(run_id, request, progress=report),
                         inputs=request.model_dump(), run_id=run_id)
