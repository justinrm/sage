from pathlib import Path

from sage_sim.models import InferenceRequest
from sage_sim.reporting.charts import (
    save_deadline_miss_rate_chart,
    save_dropped_requests_chart,
    save_latency_distribution_chart,
    save_queue_depth_over_time_chart,
    save_queue_wait_comparison_chart,
    save_throughput_comparison_chart,
    save_utilization_comparison_chart,
)
from sage_sim.reporting.paths import (
    ensure_reports_dir,
    relative_report_path,
    report_output_path,
)


def _completed_request(
    request_id: str,
    *,
    arrival_ms: int,
    start_ms: int,
    finish_ms: int,
) -> InferenceRequest:
    return InferenceRequest(
        request_id=request_id,
        model_name="model-a",
        arrival_time_ms=arrival_ms,
        estimated_runtime_ms=max(1, finish_ms - start_ms),
        estimated_tokens=128,
        status="completed",
        queue_enter_time_ms=arrival_ms,
        start_time_ms=start_ms,
        finish_time_ms=finish_ms,
    )


def test_reporting_chart_helpers_write_output_files(tmp_path: Path) -> None:
    completed_requests = [
        _completed_request("r1", arrival_ms=0, start_ms=10, finish_ms=120),
        _completed_request("r2", arrival_ms=30, start_ms=50, finish_ms=250),
    ]
    queue_depth_events = [(0, 0), (10, 1), (30, 2), (60, 0)]
    policy_rows = [
        {
            "policy": "fifo",
            "throughput_rps": 4.2,
            "dropped_request_rate": 0.05,
            "dropped_requests": 3,
            "deadline_miss_rate": 0.20,
            "p95_queue_wait_ms": 120.0,
            "gpu_utilization": 0.60,
            "cpu_utilization": 0.35,
        },
        {
            "policy": "shortest_job_first",
            "throughput_rps": 4.8,
            "dropped_request_rate": 0.02,
            "dropped_requests": 1,
            "deadline_miss_rate": 0.10,
            "p95_queue_wait_ms": 80.0,
            "gpu_utilization": 0.64,
            "cpu_utilization": 0.29,
        },
    ]

    output_paths = [
        tmp_path / "latency.png",
        tmp_path / "queue_depth.png",
        tmp_path / "utilization.png",
        tmp_path / "throughput.png",
        tmp_path / "drop_rate.png",
        tmp_path / "drop_count.png",
        tmp_path / "deadline_miss.png",
        tmp_path / "queue_wait.png",
    ]

    save_latency_distribution_chart(completed_requests, output_paths[0])
    save_queue_depth_over_time_chart(queue_depth_events, output_paths[1])
    save_utilization_comparison_chart(policy_rows, output_paths[2])
    save_throughput_comparison_chart(policy_rows, output_paths[3])
    save_dropped_requests_chart(policy_rows, output_paths[4], use_rate=True)
    save_dropped_requests_chart(policy_rows, output_paths[5], use_rate=False)
    save_deadline_miss_rate_chart(policy_rows, output_paths[6])
    save_queue_wait_comparison_chart(policy_rows, output_paths[7])

    for output_path in output_paths:
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_reporting_chart_helpers_handle_empty_inputs(tmp_path: Path) -> None:
    output_paths = [
        tmp_path / "latency_empty.png",
        tmp_path / "queue_depth_empty.png",
        tmp_path / "utilization_empty.png",
        tmp_path / "throughput_empty.png",
        tmp_path / "drop_empty.png",
        tmp_path / "deadline_empty.png",
        tmp_path / "queue_wait_empty.png",
    ]

    save_latency_distribution_chart([], output_paths[0])
    save_queue_depth_over_time_chart([], output_paths[1])
    save_utilization_comparison_chart([], output_paths[2])
    save_throughput_comparison_chart([], output_paths[3])
    save_dropped_requests_chart([], output_paths[4], use_rate=True)
    save_deadline_miss_rate_chart([], output_paths[5])
    save_queue_wait_comparison_chart([], output_paths[6])

    for output_path in output_paths:
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_report_paths_are_deterministic() -> None:
    filename = "policy_comparison_summary.csv"
    reports_dir = ensure_reports_dir()
    output_path = report_output_path(filename)

    assert reports_dir.is_dir()
    assert output_path == reports_dir / filename
    assert relative_report_path(filename) == Path("reports") / filename
