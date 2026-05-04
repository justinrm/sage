"""Core data models for simulation requests, results, and config."""

from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class InferenceRequest:
    """Incoming request representation used by schedulers and simulation."""

    request_id: str
    model_name: str
    arrival_time_ms: int
    estimated_runtime_ms: int
    estimated_tokens: int
    priority: int = 0
    requires_gpu: bool = True
    tenant_id: str | None = None
    deadline_ms: int | None = None
    status: Literal["queued", "running", "completed", "dropped"] = "queued"
    queue_enter_time_ms: int | None = None
    start_time_ms: int | None = None
    finish_time_ms: int | None = None
    dropped_reason: str | None = None


@dataclass(slots=True)
class CompletedRequest:
    """Record for completed request metrics computation."""

    request_id: str
    arrival_time_ms: int
    queue_enter_time_ms: int
    start_time_ms: int
    finish_time_ms: int
    used_gpu: bool


@dataclass(slots=True)
class ResourceConfig:
    """Simulation resource assumptions for worker pools and costs."""

    gpu_workers: int
    cpu_workers: int
    cost_per_gpu_ms: float
    cost_per_cpu_ms: float

    def __post_init__(self) -> None:
        if self.gpu_workers < 0:
            msg = "gpu_workers must be >= 0"
            raise ValueError(msg)
        if self.cpu_workers < 0:
            msg = "cpu_workers must be >= 0"
            raise ValueError(msg)
        if self.cost_per_gpu_ms < 0:
            msg = "cost_per_gpu_ms must be >= 0"
            raise ValueError(msg)
        if self.cost_per_cpu_ms < 0:
            msg = "cost_per_cpu_ms must be >= 0"
            raise ValueError(msg)


@dataclass(slots=True)
class SimulationConfig:
    """Top-level simulation settings loaded from flat YAML configs."""

    random_seed: int
    simulation_duration_ms: int
    arrival_rate_per_second: float
    drop_after_wait_ms: int
    default_gpu_runtime_ms: int
    default_cpu_runtime_ms: int

    def __post_init__(self) -> None:
        if self.simulation_duration_ms <= 0:
            msg = "simulation_duration_ms must be > 0"
            raise ValueError(msg)
        if self.arrival_rate_per_second < 0:
            msg = "arrival_rate_per_second must be >= 0"
            raise ValueError(msg)
        if self.drop_after_wait_ms < 0:
            msg = "drop_after_wait_ms must be >= 0"
            raise ValueError(msg)
        if self.default_gpu_runtime_ms <= 0:
            msg = "default_gpu_runtime_ms must be > 0"
            raise ValueError(msg)
        if self.default_cpu_runtime_ms <= 0:
            msg = "default_cpu_runtime_ms must be > 0"
            raise ValueError(msg)


@dataclass(slots=True)
class RunConfig:
    """Validated top-level config container loaded from YAML."""

    simulation: SimulationConfig
    resources: ResourceConfig
    scheduler: str | None = None
