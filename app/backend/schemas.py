"""Entradas da API; a validação física permanece em ExperimentConfig."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClassicalRequest(StrictModel):
    config: dict[str, Any]
    trajectories: int = Field(default=256, ge=16, le=10000)
    substeps: int = Field(default=4, ge=1, le=30)


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
    role: Literal["signal", "raw", "calibration_zero", "calibration_one"] = "signal"
    initial_layout: list[int] | None = None
    calibration_reference: bool = False
    max_depth: int = Field(default=20000, ge=1, le=100000)
    transpiler_seed: int | None = Field(default=None, ge=0, le=4294967295)
    optimization_level: Literal[0, 1, 2, 3] = 1
    gate_twirling: bool = False
    dynamical_decoupling: bool = False


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
    interval_index: int = Field(default=1, ge=1)


class MitigationRequest(AerRequest):
    shots: int = Field(default=16384, ge=256, le=20000, multiple_of=8)
    condition_max: float = Field(default=10., ge=1., le=100.)


class IntervalRequest(StrictModel):
    method: Literal["psa", "measured"]
    kind: Literal["pe", "c2", "c3"]
    index: int = Field(ge=0)
    repetitions: int = Field(default=200, ge=20, le=2000)
    seed: int = Field(default=1234, ge=0)


class ConvergenceRequest(StrictModel):
    pass
