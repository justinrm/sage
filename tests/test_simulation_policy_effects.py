import pytest

from sage_sim.metrics.summary import summarize_requests
from sage_sim.models import InferenceRequest, ResourceConfig, SimulationConfig
from sage_sim.scheduling import create_scheduler
from sage_sim.simulation import run_simulation


def _gpu_request(
    request_id: str,
    *,
    arrival_ms: int,
    runtime_ms: int,
    priority: int = 0,
    deadline_ms: int | None = None,
) -> InferenceRequest:
    return InferenceRequest(
        request_id=request_id,
        model_name="llm-small",
        arrival_time_ms=arrival_ms,
        estimated_runtime_ms=runtime_ms,
        estimated_tokens=128,
        priority=priority,
        deadline_ms=deadline_ms,
        requires_gpu=True,
    )


def _single_gpu_simulation_config() -> SimulationConfig:
    return SimulationConfig(
        random_seed=1,
        simulation_duration_ms=1000,
        arrival_rate_per_second=0,
        drop_after_wait_ms=1000,
        default_gpu_runtime_ms=100,
        default_cpu_runtime_ms=100,
    )


def _single_gpu_resource_config() -> ResourceConfig:
    return ResourceConfig(
        gpu_workers=1,
        cpu_workers=0,
        cost_per_gpu_ms=0.001,
        cost_per_cpu_ms=0.0,
    )


def test_sjf_changes_completion_order_and_latency_under_contention() -> None:
    requests = [
        _gpu_request("running-first", arrival_ms=0, runtime_ms=100),
        _gpu_request("queued-long", arrival_ms=1, runtime_ms=90),
        _gpu_request("queued-short", arrival_ms=2, runtime_ms=10),
    ]

    fifo_result = run_simulation(
        [request for request in requests],
        _single_gpu_simulation_config(),
        _single_gpu_resource_config(),
        scheduler=create_scheduler("fifo"),
    )
    sjf_result = run_simulation(
        [
            _gpu_request("running-first", arrival_ms=0, runtime_ms=100),
            _gpu_request("queued-long", arrival_ms=1, runtime_ms=90),
            _gpu_request("queued-short", arrival_ms=2, runtime_ms=10),
        ],
        _single_gpu_simulation_config(),
        _single_gpu_resource_config(),
        scheduler=create_scheduler("shortest_job_first"),
    )

    assert [request.request_id for request in fifo_result.completed] == [
        "running-first",
        "queued-long",
        "queued-short",
    ]
    assert [request.request_id for request in sjf_result.completed] == [
        "running-first",
        "queued-short",
        "queued-long",
    ]
    assert (
        summarize_requests(sjf_result.completed)["average_latency_ms"]
        < summarize_requests(fifo_result.completed)["average_latency_ms"]
    )
    assert max(depth for _, depth in sjf_result.queue_depth_events) > 1


def test_priority_policy_starts_high_priority_backlog_first() -> None:
    result = run_simulation(
        [
            _gpu_request("running-first", arrival_ms=0, runtime_ms=100, priority=0),
            _gpu_request("low-priority", arrival_ms=1, runtime_ms=10, priority=0),
            _gpu_request("high-priority", arrival_ms=2, runtime_ms=10, priority=9),
        ],
        _single_gpu_simulation_config(),
        _single_gpu_resource_config(),
        scheduler=create_scheduler("priority"),
    )

    assert [request.request_id for request in result.completed] == [
        "running-first",
        "high-priority",
        "low-priority",
    ]
    assert result.completed[1].start_time_ms == 100


def test_deadline_aware_policy_starts_tight_deadline_backlog_first() -> None:
    result = run_simulation(
        [
            _gpu_request("running-first", arrival_ms=0, runtime_ms=100),
            _gpu_request("loose-deadline", arrival_ms=1, runtime_ms=10, deadline_ms=500),
            _gpu_request("tight-deadline", arrival_ms=2, runtime_ms=10, deadline_ms=150),
        ],
        _single_gpu_simulation_config(),
        _single_gpu_resource_config(),
        scheduler=create_scheduler("deadline_aware"),
    )

    assert [request.request_id for request in result.completed] == [
        "running-first",
        "tight-deadline",
        "loose-deadline",
    ]
    assert result.completed[1].finish_time_ms == pytest.approx(110)
