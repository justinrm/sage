"""Run baseline simulation and write CSV/chart artifacts to reports/."""

from pathlib import Path

from sage_sim.config import load_config
from sage_sim.metrics.summary import summarize_simulation
from sage_sim.reporting.charts import (
    save_latency_distribution_chart,
    save_queue_depth_over_time_chart,
)
from sage_sim.reporting.export import export_requests_to_csv, export_summary_to_csv
from sage_sim.reporting.paths import relative_report_path, report_output_path
from sage_sim.scheduling import create_scheduler
from sage_sim.simulation import run_simulation
from sage_sim.workload import generate_synthetic_requests


def main() -> None:
    """Run baseline configuration and save deterministic report files."""
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "configs/baseline.yaml"
    config = load_config(config_path)

    requests = generate_synthetic_requests(config.simulation)
    scheduler_name = config.scheduler if config.scheduler is not None else "fifo"
    result = run_simulation(
        requests=requests,
        simulation_config=config.simulation,
        resource_config=config.resources,
        scheduler=create_scheduler(scheduler_name),
    )
    summary = summarize_simulation(result=result, resource_config=config.resources)

    requests_csv_path = report_output_path("baseline_requests.csv")
    summary_csv_path = report_output_path("baseline_summary.csv")
    latency_chart_path = report_output_path("latency_distribution_baseline.png")
    queue_depth_chart_path = report_output_path("queue_depth_baseline.png")

    export_requests_to_csv(result.completed + result.dropped, requests_csv_path)
    export_summary_to_csv(summary, summary_csv_path)
    save_latency_distribution_chart(result.completed, latency_chart_path)
    save_queue_depth_over_time_chart(result.queue_depth_events, queue_depth_chart_path)

    print("Baseline simulation complete.")
    print(f"Scheduler: {scheduler_name}")
    print("Wrote baseline outputs:")
    print(f"- {relative_report_path('baseline_requests.csv')}")
    print(f"- {relative_report_path('baseline_summary.csv')}")
    print(f"- {relative_report_path('latency_distribution_baseline.png')}")
    print(f"- {relative_report_path('queue_depth_baseline.png')}")


if __name__ == "__main__":
    main()
