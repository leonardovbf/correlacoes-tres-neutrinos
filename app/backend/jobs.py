"""Execuções em segundo plano com eventos reais do motor científico."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from . import service
from .schemas import ClassicalRequest, HardwareRequest, QuantumRequest


class JobManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="neutrino-job")
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}

    def start(self, kind: str, operation: Callable[[Callable[[dict], None]], dict]) -> dict:
        job_id = uuid4().hex[:16]
        job = {"job_id": job_id, "kind": kind, "status": "queued", "events": [],
               "run_id": None, "error": None,
               "created_utc": datetime.now(timezone.utc).isoformat()}
        with self.lock:
            self.jobs[job_id] = job
            if len(self.jobs) > 100:
                finished = [key for key, value in self.jobs.items()
                            if value["status"] in ("completed", "failed") and key != job_id]
                for key in finished[:len(self.jobs) - 100]:
                    self.jobs.pop(key, None)

        def report(event: dict) -> None:
            with self.lock:
                job["events"].append(event)

        def run() -> None:
            with self.lock:
                job["status"] = "running"
            try:
                result = operation(report)
                with self.lock:
                    job["run_id"] = result["run_id"]
                    job["status"] = "completed"
            except Exception as exc:
                with self.lock:
                    job["error"] = str(exc)
                    job["status"] = "failed"

        self.executor.submit(run)
        return self.get(job_id)

    def get(self, job_id: str) -> dict:
        with self.lock:
            job = self.jobs[job_id]
            return {**job, "events": list(job["events"])}


manager = JobManager()


def start_classical(request: ClassicalRequest) -> dict:
    return manager.start("classical", lambda report: service.create_experiment(request, progress=report))


def start_quantum(run_id: str, request: QuantumRequest) -> dict:
    # Falhas de identificador retornam imediatamente ao cliente.
    service.store.load_metadata(run_id)
    return manager.start("quantum", lambda report: service.run_quantum(run_id, request, progress=report))


def start_hardware(run_id: str, request: HardwareRequest) -> dict:
    service.store.load_metadata(run_id)
    return manager.start("hardware", lambda report: service.submit_hardware(run_id, request, progress=report))
