"""Command-line entry points for running SAGE experiments."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from sage_sim.config import load_config
from sage_sim.metrics.summary import summarize_by_field, summarize_simulation
from sage_sim.models import InferenceRequest, RunConfig
from sage_sim.reporting.charts import (
    save_deadline_miss_rate_chart,
    save_dropped_requests_chart,
    save_latency_distribution_chart,
    save_queue_depth_over_time_chart,
    save_queue_wait_comparison_chart,
    save_throughput_comparison_chart,
    save_utilization_comparison_chart,
)
from sage_sim.reporting.export import (
    export_records_to_csv,
    export_requests_to_csv,
    export_summary_to_csv,
)
from sage_sim.reporting.paths import relative_report_path, report_output_path
from sage_sim.scheduling import canonical_scheduler_name, create_scheduler
from sage_sim.simulation import run_simulation
from sage_sim.workload import generate_synthetic_requests, load_requests_from_csv

_DEFAULT_POLICIES = (
    "fifo",
    "shortest_job_first",
    "priority",
    "deadline_aware",
    "batch_by_model",
)


def _load_requests(config: RunConfig, requests_csv: Path | None) -> list[InferenceRequest]:
    if requests_csv is not None:
        return load_requests_from_csv(requests_csv)
    return generate_synthetic_requests(config.simulation)


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("config", type=Path, help="Path to a YAML run config.")
    parser.add_argument(
        "--requests-csv",
        type=Path,
        help="Optional request CSV. If omitted, synthetic requests are generated from config.",
    )


def _run_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    scheduler_name = args.scheduler or config.scheduler or "fifo"
    canonical_name = canonical_scheduler_name(scheduler_name)
    requests = _load_requests(config, args.requests_csv)
    result = run_simulation(
        requests=requests,
        simulation_config=config.simulation,
        resource_config=config.resources,
        scheduler=create_scheduler(scheduler_name),
    )
    summary = summarize_simulation(result=result, resource_config=config.resources)

    prefix = args.output_prefix or args.config.stem
    requests_csv_path = report_output_path(f"{prefix}_{canonical_name}_requests.csv")
    summary_csv_path = report_output_path(f"{prefix}_{canonical_name}_summary.csv")
    latency_chart_path = report_output_path(f"{prefix}_{canonical_name}_latency_distribution.png")
    queue_depth_chart_path = report_output_path(f"{prefix}_{canonical_name}_queue_depth.png")

    export_requests_to_csv(result.completed + result.dropped, requests_csv_path)
    export_summary_to_csv(summary, summary_csv_path)
    save_latency_distribution_chart(result.completed, latency_chart_path)
    save_queue_depth_over_time_chart(result.queue_depth_events, queue_depth_chart_path)

    print(f"Ran scheduler: {canonical_name}")
    print(f"- {relative_report_path(requests_csv_path.name)}")
    print(f"- {relative_report_path(summary_csv_path.name)}")
    print(f"- {relative_report_path(latency_chart_path.name)}")
    print(f"- {relative_report_path(queue_depth_chart_path.name)}")


def _compare_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    base_requests = _load_requests(config, args.requests_csv)
    policies = tuple(args.policies or _DEFAULT_POLICIES)
    summary_rows: list[dict[str, Any]] = []
    tenant_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []

    for policy_name in policies:
        canonical_name = canonical_scheduler_name(policy_name)
        result = run_simulation(
            requests=deepcopy(base_requests),
            simulation_config=config.simulation,
            resource_config=config.resources,
            scheduler=create_scheduler(policy_name),
        )
        summary_rows.append(
            {
                "policy": canonical_name,
                **summarize_simulation(result=result, resource_config=config.resources),
            }
        )
        completed_and_dropped = result.completed + result.dropped
        tenant_rows.extend(
            {"policy": canonical_name, **row}
            for row in summarize_by_field(completed_and_dropped, field_name="tenant_id")
        )
        model_rows.extend(
            {"policy": canonical_name, **row}
            for row in summarize_by_field(completed_and_dropped, field_name="model_name")
        )

    prefix = args.output_prefix or args.config.stem
    summary_csv_path = report_output_path(f"{prefix}_policy_comparison_summary.csv")
    tenant_csv_path = report_output_path(f"{prefix}_policy_tenant_summary.csv")
    model_csv_path = report_output_path(f"{prefix}_policy_model_summary.csv")
    utilization_chart_path = report_output_path(f"{prefix}_utilization_by_policy.png")
    throughput_chart_path = report_output_path(f"{prefix}_throughput_by_policy.png")
    dropped_chart_path = report_output_path(f"{prefix}_dropped_rate_by_policy.png")
    deadline_chart_path = report_output_path(f"{prefix}_deadline_miss_rate_by_policy.png")
    queue_wait_chart_path = report_output_path(f"{prefix}_p95_queue_wait_by_policy.png")

    export_records_to_csv(records=summary_rows, path=summary_csv_path)
    export_records_to_csv(records=tenant_rows, path=tenant_csv_path)
    export_records_to_csv(records=model_rows, path=model_csv_path)
    save_utilization_comparison_chart(summary_rows, utilization_chart_path)
    save_throughput_comparison_chart(summary_rows, throughput_chart_path)
    save_dropped_requests_chart(summary_rows, dropped_chart_path, use_rate=True)
    save_deadline_miss_rate_chart(summary_rows, deadline_chart_path)
    save_queue_wait_comparison_chart(summary_rows, queue_wait_chart_path)

    print("Policy comparison complete.")
    print(f"- {relative_report_path(summary_csv_path.name)}")
    print(f"- {relative_report_path(tenant_csv_path.name)}")
    print(f"- {relative_report_path(model_csv_path.name)}")
    print(f"- {relative_report_path(utilization_chart_path.name)}")
    print(f"- {relative_report_path(throughput_chart_path.name)}")
    print(f"- {relative_report_path(dropped_chart_path.name)}")
    print(f"- {relative_report_path(deadline_chart_path.name)}")
    print(f"- {relative_report_path(queue_wait_chart_path.name)}")


def build_parser() -> argparse.ArgumentParser:
    """Build the SAGE command-line parser."""
    parser = argparse.ArgumentParser(prog="sage-sim")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one scheduler policy.")
    _add_common_arguments(run_parser)
    run_parser.add_argument(
        "--scheduler",
        help="Scheduler name. Defaults to config scheduler or FIFO.",
    )
    run_parser.add_argument("--output-prefix", help="Prefix for generated report filenames.")
    run_parser.set_defaults(func=_run_command)

    compare_parser = subparsers.add_parser("compare", help="Compare scheduler policies.")
    _add_common_arguments(compare_parser)
    compare_parser.add_argument(
        "--policies",
        nargs="+",
        help="Policy names to compare. Defaults to all implemented policies.",
    )
    compare_parser.add_argument("--output-prefix", help="Prefix for generated report filenames.")
    compare_parser.set_defaults(func=_compare_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the SAGE command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
