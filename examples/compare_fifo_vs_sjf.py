"""Compare scheduler policies on the same workload."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd

from sage_sim.config import load_config
from sage_sim.metrics.summary import summarize_by_field, summarize_simulation
from sage_sim.models import InferenceRequest
from sage_sim.reporting.charts import (
    save_deadline_miss_rate_chart,
    save_dropped_requests_chart,
    save_latency_distribution_chart,
    save_queue_wait_comparison_chart,
    save_throughput_comparison_chart,
    save_utilization_comparison_chart,
)
from sage_sim.reporting.export import export_records_to_csv
from sage_sim.reporting.paths import relative_report_path, report_output_path
from sage_sim.scheduling import canonical_scheduler_name, create_scheduler
from sage_sim.simulation import run_simulation
from sage_sim.workload import load_requests_from_csv

_POLICIES_TO_COMPARE = (
    "fifo",
    "shortest_job_first",
    "priority",
    "deadline_aware",
    "batch_by_model",
)


def _build_policy_summary_rows() -> tuple[
    list[dict[str, Any]],
    list[InferenceRequest],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Run all configured policies on an equivalent workload."""
    project_root = Path(__file__).resolve().parents[1]
    run_config = load_config(project_root / "configs/stress.yaml")

    base_requests = load_requests_from_csv(project_root / "data/stress_requests.csv")
    summary_rows: list[dict[str, Any]] = []
    baseline_completed: list[InferenceRequest] = []
    tenant_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []

    for policy_name in _POLICIES_TO_COMPARE:
        policy_requests = deepcopy(base_requests)
        result = run_simulation(
            requests=policy_requests,
            simulation_config=run_config.simulation,
            resource_config=run_config.resources,
            scheduler=create_scheduler(policy_name),
        )
        summary = summarize_simulation(result=result, resource_config=run_config.resources)
        canonical_name = canonical_scheduler_name(policy_name)
        summary_rows.append({"policy": canonical_name, **summary})
        completed_and_dropped = result.completed + result.dropped
        tenant_rows.extend(
            {"policy": canonical_name, **row}
            for row in summarize_by_field(completed_and_dropped, field_name="tenant_id")
        )
        model_rows.extend(
            {"policy": canonical_name, **row}
            for row in summarize_by_field(completed_and_dropped, field_name="model_name")
        )
        if canonical_name == "fifo":
            baseline_completed = list(result.completed)

    return summary_rows, baseline_completed, tenant_rows, model_rows


def _format_comparison_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Return a rounded policy comparison table for terminal output."""
    display_columns = [
        "policy",
        "average_latency_ms",
        "p95_latency_ms",
        "p95_queue_wait_ms",
        "max_queue_wait_ms",
        "deadline_miss_rate",
        "throughput_rps",
        "dropped_request_rate",
        "gpu_utilization",
        "cpu_utilization",
        "cost_per_request",
    ]
    frame = pd.DataFrame(rows)[display_columns].copy()
    round_columns = [column for column in display_columns if column != "policy"]
    frame[round_columns] = frame[round_columns].round(4)
    return frame


def main() -> None:
    """Run policy comparison and export CSV/charts to reports/."""
    rows, baseline_completed, tenant_rows, model_rows = _build_policy_summary_rows()
    output_table = _format_comparison_table(rows)
    print("Policy comparison (same curated stress workload):")
    print(output_table.to_string(index=False))

    summary_csv_path = report_output_path("policy_comparison_summary.csv")
    tenant_csv_path = report_output_path("policy_tenant_summary.csv")
    model_csv_path = report_output_path("policy_model_summary.csv")
    utilization_chart_path = report_output_path("utilization_by_policy.png")
    throughput_chart_path = report_output_path("throughput_by_policy.png")
    dropped_chart_path = report_output_path("dropped_rate_by_policy.png")
    deadline_chart_path = report_output_path("deadline_miss_rate_by_policy.png")
    queue_wait_chart_path = report_output_path("p95_queue_wait_by_policy.png")
    latency_chart_path = report_output_path("latency_distribution_fifo.png")

    export_records_to_csv(records=rows, path=summary_csv_path)
    export_records_to_csv(records=tenant_rows, path=tenant_csv_path)
    export_records_to_csv(records=model_rows, path=model_csv_path)
    save_utilization_comparison_chart(rows, utilization_chart_path)
    save_throughput_comparison_chart(rows, throughput_chart_path)
    save_dropped_requests_chart(rows, dropped_chart_path, use_rate=True)
    save_deadline_miss_rate_chart(rows, deadline_chart_path)
    save_queue_wait_comparison_chart(rows, queue_wait_chart_path)
    save_latency_distribution_chart(baseline_completed, latency_chart_path)

    print("Wrote policy comparison outputs:")
    print(f"- {relative_report_path('policy_comparison_summary.csv')}")
    print(f"- {relative_report_path('policy_tenant_summary.csv')}")
    print(f"- {relative_report_path('policy_model_summary.csv')}")
    print(f"- {relative_report_path('utilization_by_policy.png')}")
    print(f"- {relative_report_path('throughput_by_policy.png')}")
    print(f"- {relative_report_path('dropped_rate_by_policy.png')}")
    print(f"- {relative_report_path('deadline_miss_rate_by_policy.png')}")
    print(f"- {relative_report_path('p95_queue_wait_by_policy.png')}")
    print(f"- {relative_report_path('latency_distribution_fifo.png')}")


if __name__ == "__main__":
    main()
