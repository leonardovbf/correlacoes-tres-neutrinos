"""Entradas da API; a validação física permanece em ExperimentConfig."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClassicalRequest(StrictModel):
    config: dict[str, Any]
    trajectories: int = Field(default=256, ge=16, le=4096)
    substeps: int = Field(default=4, ge=1, le=12)


class QuantumRequest(StrictModel):
    steps: int = Field(default=2, ge=1, le=16)
    shots: int = Field(default=1024, ge=32, le=20000)
    readout_error: float = Field(default=0.02, ge=0, le=0.25)


class HardwareRequest(StrictModel):
    backend: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    interval_index: int = Field(default=1, ge=1)
    steps: int = Field(default=2, ge=1, le=16)
    shots: int = Field(default=1024, ge=32, le=20000)
    kind: Literal["pe", "c2", "c3"] = "pe"
    index: int = Field(default=0, ge=0)


class AerRequest(StrictModel):
    interval_index: int = Field(default=5, ge=1)
    steps: int = Field(default=2, ge=1, le=16)
    shots: int = Field(default=1024, ge=32, le=20000)
    single_qubit_error: float = Field(default=0.001, ge=0, le=0.25)
    two_qubit_error: float = Field(default=0.01, ge=0, le=0.25)
    readout_error: float = Field(default=0.02, ge=0, le=0.25)
    kind: Literal["pe", "c2", "c3"] = "pe"
    index: int = Field(default=0, ge=0)


class CircuitRequest(StrictModel):
    steps: int = Field(default=2, ge=1, le=16)


class IntervalRequest(StrictModel):
    method: Literal["psa", "measured"]
    kind: Literal["pe", "c2", "c3"]
    index: int = Field(ge=0)


class ConvergenceRequest(StrictModel):
    pass
