"""Configuration loading for SAGE."""

from pathlib import Path
from typing import Any

import yaml

from sage_sim.models import ResourceConfig, RunConfig, SimulationConfig


def _require_int(data: dict[str, Any], key: str, path: Path) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        msg = f"Expected integer '{key}' in config file: {path}"
        raise ValueError(msg)
    return value


def _require_float(data: dict[str, Any], key: str, path: Path) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        msg = f"Expected number '{key}' in config file: {path}"
        raise ValueError(msg)
    return float(value)


def load_config(path: Path) -> RunConfig:
    """Load and validate a YAML configuration file.

    The project currently keeps a flat YAML shape for simplicity. This loader
    validates required keys and maps them into typed dataclasses.
    """
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        msg = f"Expected mapping at root of config file: {path}"
        raise ValueError(msg)

    simulation = SimulationConfig(
        random_seed=_require_int(data, "random_seed", path),
        simulation_duration_ms=_require_int(data, "simulation_duration_ms", path),
        arrival_rate_per_second=_require_float(data, "arrival_rate_per_second", path),
        drop_after_wait_ms=_require_int(data, "drop_after_wait_ms", path),
        default_gpu_runtime_ms=_require_int(data, "default_gpu_runtime_ms", path),
        default_cpu_runtime_ms=_require_int(data, "default_cpu_runtime_ms", path),
    )
    resources = ResourceConfig(
        gpu_workers=_require_int(data, "gpu_workers", path),
        cpu_workers=_require_int(data, "cpu_workers", path),
        cost_per_gpu_ms=_require_float(data, "cost_per_gpu_ms", path),
        cost_per_cpu_ms=_require_float(data, "cost_per_cpu_ms", path),
    )
    scheduler = data.get("scheduler")
    if scheduler is not None and not isinstance(scheduler, str):
        msg = f"Expected optional string 'scheduler' in config file: {path}"
        raise ValueError(msg)

    return RunConfig(simulation=simulation, resources=resources, scheduler=scheduler)
