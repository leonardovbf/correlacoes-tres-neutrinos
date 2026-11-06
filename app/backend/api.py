"""API HTTP local do laboratório. Iniciar com uvicorn app.backend.api:app."""

from __future__ import annotations

import subprocess

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import audit, ibm_runtime, jobs, service
from .schemas import (AerRequest, CircuitRequest, ClassicalRequest, ConvergenceRequest,
                      HardwareRequest, IntervalRequest, QuantumRequest)
from .storage import RunNotFound


app = FastAPI(title="Laboratório de Neutrinos", version="0.2.0",
              description="API local para comparações exatas, PSA e circuitos quânticos.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RunNotFound)
async def missing_run(_request, _exc):
    return JSONResponse(status_code=404, content={"detail": "Experimento não encontrado",
                                                "execution_id": getattr(_exc, "execution_id", None)})


@app.exception_handler(ValueError)
async def invalid_input(_request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": audit.safe_error(exc)["message"],
                                                "execution_id": getattr(exc, "execution_id", None)})


@app.exception_handler(subprocess.TimeoutExpired)
async def worker_timeout(_request, _exc):
    return JSONResponse(status_code=504, content={"detail": "O cálculo Qiskit excedeu 120 segundos",
                                                "execution_id": getattr(_exc, "execution_id", None)})


@app.exception_handler(RuntimeError)
async def worker_failure(_request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": audit.safe_error(exc)["message"],
                                                "execution_id": getattr(exc, "execution_id", None)})


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "python", "storage": "results/"}


@app.get("/api/ibm/status")
def ibm_status():
    return ibm_runtime.status()


@app.get("/api/ibm/backends")
def ibm_backends(min_qubits: int = Query(default=2, ge=2, le=8)):
    return ibm_runtime.list_backends(min_qubits)


@app.get("/api/scenarios/example")
def scenario():
    return service.example_scenario()


@app.post("/api/jobs/classical", status_code=202)
def start_classical(request: ClassicalRequest):
    return jobs.start_classical(request)


@app.post("/api/jobs/{run_id}/quantum", status_code=202)
def start_quantum(run_id: str, request: QuantumRequest):
    return jobs.start_quantum(run_id, request)


@app.post("/api/jobs/{run_id}/hardware", status_code=202)
def start_hardware(run_id: str, request: HardwareRequest):
    return jobs.start_hardware(run_id, request)


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    try:
        return jobs.manager.get(job_id)
    except KeyError:
        return JSONResponse(status_code=404, content={"detail": "Execução não encontrada"})


@app.post("/api/experiments", status_code=201)
def create(request: ClassicalRequest):
    return service.create_experiment(request)


@app.get("/api/experiments/{run_id}")
def get(run_id: str):
    return service.get_experiment(run_id)


@app.get("/api/experiments/{run_id}/manifest")
def manifest(run_id: str):
    metadata, _ = service.store.load_metadata(run_id)
    return metadata


@app.get("/api/executions/{execution_id}")
def execution_record(execution_id: str):
    try:
        return audit.load_execution(service.store.root, execution_id)
    except KeyError:
        return JSONResponse(status_code=404, content={"detail": "Registro de execução não encontrado"})


@app.get("/api/experiments/{run_id}/executions")
def experiment_executions(run_id: str):
    service.store.load_metadata(run_id)
    return audit.execution_history(service.store.root, run_id)


@app.get("/api/experiments/{run_id}/hardware/{job_id}")
def hardware_job(run_id: str, job_id: str):
    return service.refresh_hardware(run_id, job_id)


@app.post("/api/experiments/{run_id}/quantum")
def quantum(run_id: str, request: QuantumRequest):
    return service.run_quantum(run_id, request)


@app.post("/api/experiments/{run_id}/interval")
def interval(run_id: str, request: IntervalRequest):
    return service.get_interval(run_id, request)


@app.post("/api/experiments/{run_id}/circuit")
def circuit(run_id: str, request: CircuitRequest):
    return service.verify_circuit(run_id, request)


@app.post("/api/experiments/{run_id}/aer")
def aer(run_id: str, request: AerRequest):
    return service.run_aer(run_id, request)


@app.post("/api/experiments/{run_id}/convergence")
def convergence(run_id: str, _request: ConvergenceRequest):
    return service.run_convergence(run_id)
