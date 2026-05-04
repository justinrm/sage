"""Workload generation and CSV-loading helpers."""

from pathlib import Path
from typing import Any

import pandas as pd

from sage_sim.models import InferenceRequest, SimulationConfig
from sage_sim.utils.random import build_rng

_REQUIRED_CSV_COLUMNS = {
    "request_id",
    "model_name",
    "arrival_time_ms",
    "estimated_runtime_ms",
    "estimated_tokens",
    "priority",
    "requires_gpu",
    "tenant_id",
    "deadline_ms",
}


def _parse_required_int(value: Any, field_name: str, row_number: int, path: Path) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        msg = f"Invalid integer for '{field_name}' at row {row_number} in {path}"
        raise ValueError(msg) from error


def _parse_optional_int(value: Any, field_name: str, row_number: int, path: Path) -> int | None:
    if pd.isna(value) or value == "":
        return None
    return _parse_required_int(value, field_name, row_number, path)


def _parse_optional_str(value: Any) -> str | None:
    if pd.isna(value) or value == "":
        return None
    return str(value)


def _parse_bool(value: Any, field_name: str, row_number: int, path: Path) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    msg = f"Invalid boolean for '{field_name}' at row {row_number} in {path}"
    raise ValueError(msg)


def load_requests_from_csv(path: Path) -> list[InferenceRequest]:
    """Load requests from CSV with schema checks and row-level validation."""
    frame = pd.read_csv(path)
    missing_columns = sorted(_REQUIRED_CSV_COLUMNS - set(frame.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        msg = f"Missing required CSV columns in {path}: {missing}"
        raise ValueError(msg)

    requests: list[InferenceRequest] = []
    for row_index, row in enumerate(frame.to_dict(orient="records"), start=2):
        requests.append(
            InferenceRequest(
                request_id=str(row["request_id"]),
                tenant_id=_parse_optional_str(row["tenant_id"]),
                model_name=str(row["model_name"]),
                arrival_time_ms=_parse_required_int(
                    row["arrival_time_ms"], "arrival_time_ms", row_index, path
                ),
                estimated_runtime_ms=_parse_required_int(
                    row["estimated_runtime_ms"], "estimated_runtime_ms", row_index, path
                ),
                estimated_tokens=_parse_required_int(
                    row["estimated_tokens"], "estimated_tokens", row_index, path
                ),
                priority=_parse_required_int(row["priority"], "priority", row_index, path),
                deadline_ms=_parse_optional_int(row["deadline_ms"], "deadline_ms", row_index, path),
                requires_gpu=_parse_bool(row["requires_gpu"], "requires_gpu", row_index, path),
            )
        )
    return requests


def generate_synthetic_requests(
    config: SimulationConfig,
    *,
    max_requests: int | None = None,
) -> list[InferenceRequest]:
    """Generate deterministic synthetic requests from simulation config."""
    if max_requests is not None and max_requests <= 0:
        return []

    rng = build_rng(config.random_seed)
    arrivals_per_ms = config.arrival_rate_per_second / 1000.0
    if arrivals_per_ms <= 0:
        return []

    requests: list[InferenceRequest] = []
    current_time_ms = 0
    request_index = 0
    model_names = ("llm-small", "llm-medium", "llm-large")
    token_options = (128, 256, 384, 512, 768, 1024)

    while current_time_ms < config.simulation_duration_ms:
        interarrival_ms = max(1, int(round(rng.expovariate(arrivals_per_ms))))
        current_time_ms += interarrival_ms
        if current_time_ms >= config.simulation_duration_ms:
            break

        requires_gpu = rng.random() < 0.75
        runtime_baseline = (
            config.default_gpu_runtime_ms if requires_gpu else config.default_cpu_runtime_ms
        )
        jitter_ratio = 0.8 + (rng.random() * 0.4)
        estimated_runtime_ms = max(1, int(round(runtime_baseline * jitter_ratio)))

        requests.append(
            InferenceRequest(
                request_id=f"synthetic-{config.random_seed}-{request_index:05d}",
                model_name=rng.choice(model_names),
                arrival_time_ms=current_time_ms,
                estimated_runtime_ms=estimated_runtime_ms,
                estimated_tokens=rng.choice(token_options),
                priority=rng.randint(0, 4),
                requires_gpu=requires_gpu,
            )
        )
        request_index += 1
        if max_requests is not None and len(requests) >= max_requests:
            break

    return requests
