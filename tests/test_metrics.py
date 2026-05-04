import pandas as pd
import pytest

from sage_sim.metrics.summary import (
    summarize_by_field,
    summarize_deadlines,
    summarize_requests,
    summarize_simulation,
)
from sage_sim.models import InferenceRequest, ResourceConfig
from sage_sim.reporting.export import export_requests_to_csv, export_summary_to_csv
from sage_sim.simulation import SimulationResult


def _completed_request(
    request_id: str,
    *,
    queue_enter_ms: int,
    start_ms: int,
    finish_ms: int,
    requires_gpu: bool = True,
) -> InferenceRequest:
    return InferenceRequest(
        request_id=request_id,
        model_name="model-a",
        arrival_time_ms=0,
        estimated_runtime_ms=max(1, finish_ms - start_ms),
        estimated_tokens=128,
        requires_gpu=requires_gpu,
        status="completed",
        queue_enter_time_ms=queue_enter_ms,
        start_time_ms=start_ms,
        finish_time_ms=finish_ms,
    )


def test_summarize_requests_computes_latency_queue_wait_and_service_time() -> None:
    completed = [
        _completed_request("r1", queue_enter_ms=0, start_ms=10, finish_ms=100),
        _completed_request("r2", queue_enter_ms=0, start_ms=20, finish_ms=300),
        _completed_request("r3", queue_enter_ms=0, start_ms=30, finish_ms=500),
    ]

    summary = summarize_requests(completed)

    assert summary["completed_requests"] == 3
    assert summary["average_latency_ms"] == pytest.approx(300.0)
    assert summary["p95_latency_ms"] == pytest.approx(480.0)
    assert summary["average_queue_wait_ms"] == pytest.approx(20.0)
    assert summary["p95_queue_wait_ms"] == pytest.approx(29.0)
    assert summary["max_queue_wait_ms"] == pytest.approx(30.0)
    assert summary["average_service_time_ms"] == pytest.approx(280.0)


def test_summarize_simulation_computes_throughput_drop_utilization_and_cost() -> None:
    completed = [
        _completed_request("gpu-1", queue_enter_ms=0, start_ms=0, finish_ms=300, requires_gpu=True),
        _completed_request(
            "cpu-1",
            queue_enter_ms=50,
            start_ms=100,
            finish_ms=350,
            requires_gpu=False,
        ),
    ]
    dropped = [
        InferenceRequest(
            request_id="drop-1",
            model_name="model-a",
            arrival_time_ms=250,
            estimated_runtime_ms=200,
            estimated_tokens=64,
            status="dropped",
            finish_time_ms=700,
            dropped_reason="wait_timeout",
        )
    ]
    result = SimulationResult(
        completed=completed,
        dropped=dropped,
        simulation_duration_ms=2000,
        total_gpu_busy_ms=500,
        total_cpu_busy_ms=250,
    )
    resources = ResourceConfig(
        gpu_workers=2,
        cpu_workers=1,
        cost_per_gpu_ms=0.01,
        cost_per_cpu_ms=0.001,
    )

    summary = summarize_simulation(result, resources)

    assert summary["completed_requests"] == 2
    assert summary["dropped_requests"] == 1
    assert summary["total_requests"] == 3
    assert summary["dropped_request_rate"] == pytest.approx(1 / 3)
    assert summary["throughput_rps"] == pytest.approx(1.0)
    assert summary["gpu_utilization"] == pytest.approx(0.125)
    assert summary["cpu_utilization"] == pytest.approx(0.125)
    assert summary["estimated_total_cost"] == pytest.approx(5.25)
    assert summary["cost_per_request"] == pytest.approx(2.625)


def test_metrics_empty_input_returns_safe_defaults() -> None:
    resources = ResourceConfig(
        gpu_workers=1,
        cpu_workers=1,
        cost_per_gpu_ms=0.002,
        cost_per_cpu_ms=0.001,
    )
    result = SimulationResult(completed=[], dropped=[], simulation_duration_ms=0)

    request_summary = summarize_requests([])
    simulation_summary = summarize_simulation(result, resources)

    assert request_summary["completed_requests"] == 0
    assert request_summary["average_latency_ms"] == 0.0
    assert request_summary["p95_latency_ms"] == 0.0
    assert request_summary["average_queue_wait_ms"] == 0.0
    assert request_summary["p95_queue_wait_ms"] == 0.0
    assert request_summary["max_queue_wait_ms"] == 0.0
    assert request_summary["average_service_time_ms"] == 0.0

    assert simulation_summary["throughput_rps"] == 0.0
    assert simulation_summary["dropped_request_rate"] == 0.0
    assert simulation_summary["gpu_utilization"] == 0.0
    assert simulation_summary["cpu_utilization"] == 0.0
    assert simulation_summary["estimated_total_cost"] == 0.0
    assert simulation_summary["cost_per_request"] == 0.0


def test_export_helpers_write_request_and_summary_csv(tmp_path) -> None:
    completed = [
        _completed_request("r1", queue_enter_ms=0, start_ms=10, finish_ms=100),
        _completed_request("r2", queue_enter_ms=0, start_ms=20, finish_ms=200),
    ]
    requests_path = tmp_path / "requests.csv"
    summary_path = tmp_path / "summary.csv"

    export_requests_to_csv(completed, requests_path)
    export_summary_to_csv({"completed_requests": 2, "throughput_rps": 1.5}, summary_path)

    request_frame = pd.read_csv(requests_path)
    summary_frame = pd.read_csv(summary_path)

    assert {"request_id", "status", "start_time_ms", "finish_time_ms"}.issubset(
        set(request_frame.columns)
    )
    assert len(request_frame) == 2
    assert set(summary_frame.columns) == {"completed_requests", "throughput_rps"}
    assert summary_frame.iloc[0]["completed_requests"] == 2


def test_deadline_summary_counts_completed_misses_and_dropped_requests() -> None:
    on_time = _completed_request("on-time", queue_enter_ms=0, start_ms=0, finish_ms=90)
    on_time.deadline_ms = 100
    late = _completed_request("late", queue_enter_ms=0, start_ms=0, finish_ms=140)
    late.deadline_ms = 100
    dropped = InferenceRequest(
        request_id="dropped",
        model_name="model-a",
        arrival_time_ms=0,
        estimated_runtime_ms=100,
        estimated_tokens=128,
        deadline_ms=100,
        status="dropped",
        finish_time_ms=100,
        dropped_reason="wait_timeout",
    )

    summary = summarize_deadlines([on_time, late, dropped])

    assert summary["deadline_requests"] == 3
    assert summary["deadline_misses"] == 2
    assert summary["deadline_miss_rate"] == pytest.approx(2 / 3)


def test_grouped_summary_reports_tenant_diagnostics() -> None:
    premium = _completed_request("premium", queue_enter_ms=0, start_ms=10, finish_ms=100)
    premium.tenant_id = "premium"
    standard = _completed_request("standard", queue_enter_ms=0, start_ms=80, finish_ms=200)
    standard.tenant_id = "standard"

    rows = summarize_by_field([premium, standard], field_name="tenant_id")

    assert [row["tenant_id"] for row in rows] == ["premium", "standard"]
    assert rows[0]["completed_requests"] == 1
    assert rows[1]["max_queue_wait_ms"] == pytest.approx(80.0)
