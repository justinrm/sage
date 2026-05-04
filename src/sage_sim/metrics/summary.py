"""Aggregate summary metric functions."""

from typing import Any

import pandas as pd

from sage_sim.metrics.utilization import (
    estimate_cost,
    estimate_cost_per_request,
    estimate_utilization,
)
from sage_sim.models import InferenceRequest, ResourceConfig
from sage_sim.simulation import SimulationResult


def summarize_requests(completed: list[InferenceRequest]) -> dict[str, Any]:
    """Return request-level latency summaries from completed requests."""
    if not completed:
        return {
            "completed_requests": 0,
            "average_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "average_queue_wait_ms": 0.0,
            "p95_queue_wait_ms": 0.0,
            "max_queue_wait_ms": 0.0,
            "average_service_time_ms": 0.0,
        }

    frame = pd.DataFrame(
        {
            "arrival_time_ms": [item.arrival_time_ms for item in completed],
            "queue_enter_time_ms": [item.queue_enter_time_ms for item in completed],
            "start_time_ms": [item.start_time_ms for item in completed],
            "finish_time_ms": [item.finish_time_ms for item in completed],
        }
    )

    latency_frame = frame.dropna(subset=["arrival_time_ms", "finish_time_ms"]).copy()
    if latency_frame.empty:
        average_latency_ms = 0.0
        p95_latency_ms = 0.0
    else:
        latency_frame["end_to_end_latency_ms"] = (
            latency_frame["finish_time_ms"] - latency_frame["arrival_time_ms"]
        )
        average_latency_ms = float(latency_frame["end_to_end_latency_ms"].mean())
        p95_latency_ms = float(latency_frame["end_to_end_latency_ms"].quantile(0.95))

    queue_wait_frame = frame.dropna(subset=["queue_enter_time_ms", "start_time_ms"]).copy()
    if queue_wait_frame.empty:
        average_queue_wait_ms = 0.0
        p95_queue_wait_ms = 0.0
        max_queue_wait_ms = 0.0
    else:
        queue_wait_frame["queue_wait_ms"] = (
            queue_wait_frame["start_time_ms"] - queue_wait_frame["queue_enter_time_ms"]
        )
        average_queue_wait_ms = float(queue_wait_frame["queue_wait_ms"].mean())
        p95_queue_wait_ms = float(queue_wait_frame["queue_wait_ms"].quantile(0.95))
        max_queue_wait_ms = float(queue_wait_frame["queue_wait_ms"].max())

    service_time_frame = frame.dropna(subset=["start_time_ms", "finish_time_ms"]).copy()
    if service_time_frame.empty:
        average_service_time_ms = 0.0
    else:
        service_time_frame["service_time_ms"] = (
            service_time_frame["finish_time_ms"] - service_time_frame["start_time_ms"]
        )
        average_service_time_ms = float(service_time_frame["service_time_ms"].mean())

    return {
        "completed_requests": int(len(frame)),
        "average_latency_ms": average_latency_ms,
        "p95_latency_ms": p95_latency_ms,
        "average_queue_wait_ms": average_queue_wait_ms,
        "p95_queue_wait_ms": p95_queue_wait_ms,
        "max_queue_wait_ms": max_queue_wait_ms,
        "average_service_time_ms": average_service_time_ms,
    }


def summarize_simulation(
    result: SimulationResult,
    resource_config: ResourceConfig,
) -> dict[str, Any]:
    """Return full milestone-4 summary metrics from a simulation result."""
    request_summary = summarize_requests(result.completed)
    dropped_requests = len(result.dropped)
    total_requests = request_summary["completed_requests"] + dropped_requests
    simulation_duration_seconds = max(0.0, result.simulation_duration_ms / 1000.0)
    deadline_summary = summarize_deadlines(result.completed + result.dropped)

    throughput_rps = (
        request_summary["completed_requests"] / simulation_duration_seconds
        if simulation_duration_seconds > 0
        else 0.0
    )
    dropped_request_rate = dropped_requests / total_requests if total_requests > 0 else 0.0

    gpu_utilization = estimate_utilization(
        total_busy_ms=result.total_gpu_busy_ms,
        workers=resource_config.gpu_workers,
        duration_ms=result.simulation_duration_ms,
    )
    cpu_utilization = estimate_utilization(
        total_busy_ms=result.total_cpu_busy_ms,
        workers=resource_config.cpu_workers,
        duration_ms=result.simulation_duration_ms,
    )
    estimated_total_cost = estimate_cost(
        gpu_busy_ms=result.total_gpu_busy_ms,
        cpu_busy_ms=result.total_cpu_busy_ms,
        cost_per_gpu_ms=resource_config.cost_per_gpu_ms,
        cost_per_cpu_ms=resource_config.cost_per_cpu_ms,
    )
    cost_per_request = estimate_cost_per_request(
        total_cost=estimated_total_cost,
        completed_requests=request_summary["completed_requests"],
    )

    return {
        **request_summary,
        **deadline_summary,
        "dropped_requests": dropped_requests,
        "total_requests": total_requests,
        "dropped_request_rate": float(dropped_request_rate),
        "throughput_rps": float(throughput_rps),
        "gpu_utilization": float(gpu_utilization),
        "cpu_utilization": float(cpu_utilization),
        "estimated_total_cost": float(estimated_total_cost),
        "cost_per_request": float(cost_per_request),
    }


def summarize_deadlines(requests: list[InferenceRequest]) -> dict[str, Any]:
    """Return deadline miss metrics for requests with an explicit deadline."""
    deadline_requests = [request for request in requests if request.deadline_ms is not None]
    if not deadline_requests:
        return {
            "deadline_requests": 0,
            "deadline_misses": 0,
            "deadline_miss_rate": 0.0,
        }

    deadline_misses = 0
    for request in deadline_requests:
        if request.status == "dropped":
            deadline_misses += 1
            continue
        if request.finish_time_ms is not None and request.finish_time_ms > request.deadline_ms:
            deadline_misses += 1

    return {
        "deadline_requests": len(deadline_requests),
        "deadline_misses": deadline_misses,
        "deadline_miss_rate": float(deadline_misses / len(deadline_requests)),
    }


def summarize_by_field(
    requests: list[InferenceRequest],
    *,
    field_name: str,
) -> list[dict[str, Any]]:
    """Return grouped request diagnostics for tenant or model reporting."""
    if field_name not in {"tenant_id", "model_name"}:
        msg = "field_name must be 'tenant_id' or 'model_name'"
        raise ValueError(msg)

    groups: dict[str, list[InferenceRequest]] = {}
    for request in requests:
        raw_value = getattr(request, field_name)
        group_value = "unknown" if raw_value is None else str(raw_value)
        groups.setdefault(group_value, []).append(request)

    rows: list[dict[str, Any]] = []
    for group_value in sorted(groups):
        group_requests = groups[group_value]
        completed = [request for request in group_requests if request.status == "completed"]
        dropped = [request for request in group_requests if request.status == "dropped"]
        request_summary = summarize_requests(completed)
        deadline_summary = summarize_deadlines(group_requests)
        rows.append(
            {
                field_name: group_value,
                **request_summary,
                **deadline_summary,
                "dropped_requests": len(dropped),
                "total_requests": len(group_requests),
                "dropped_request_rate": len(dropped) / len(group_requests)
                if group_requests
                else 0.0,
            }
        )
    return rows
