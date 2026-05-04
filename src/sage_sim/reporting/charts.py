"""Matplotlib chart helpers for simulation reports."""

# ruff: noqa: E402

import os
import tempfile
from pathlib import Path
from typing import Any

_CACHE_ROOT = Path(os.environ.get("SAGE_CACHE_DIR", Path(tempfile.gettempdir()) / "sage-cache"))
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sage_sim.models import InferenceRequest


def _save_figure(figure: plt.Figure, path: Path) -> None:
    """Persist a chart and close it to free matplotlib state."""
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)


def _show_empty_chart_message(axis: plt.Axes, *, message: str) -> None:
    """Render a friendly message for empty chart input."""
    axis.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=axis.transAxes,
    )


def save_latency_distribution_chart(
    completed_requests: list[InferenceRequest],
    path: Path,
    *,
    bins: int = 20,
) -> None:
    """Save end-to-end latency distribution histogram.

    Filename convention is caller-managed and deterministic (for example:
    ``latency_distribution_fifo.png``).
    """
    latencies_ms = [
        request.finish_time_ms - request.arrival_time_ms
        for request in completed_requests
        if request.finish_time_ms is not None
    ]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    if latencies_ms:
        axis.hist(latencies_ms, bins=bins, edgecolor="black")
    else:
        _show_empty_chart_message(axis, message="No completed requests to plot.")
    axis.set_title("Latency Distribution")
    axis.set_xlabel("End-to-End Latency (ms)")
    axis.set_ylabel("Request Count")
    _save_figure(figure, path)


def save_queue_depth_over_time_chart(
    queue_depth_events: list[tuple[int, int]],
    path: Path,
) -> None:
    """Save queue depth events as a time-series step chart.

    Filename convention is caller-managed and deterministic (for example:
    ``queue_depth_fifo.png``).
    """
    figure, axis = plt.subplots(figsize=(8, 4.5))
    if queue_depth_events:
        sorted_events = sorted(queue_depth_events, key=lambda event: event[0])
        times_ms = [time_ms for time_ms, _ in sorted_events]
        depths = [depth for _, depth in sorted_events]
        axis.step(times_ms, depths, where="post")
    else:
        _show_empty_chart_message(axis, message="No queue depth events to plot.")
    axis.set_title("Queue Depth Over Time")
    axis.set_xlabel("Simulation Time (ms)")
    axis.set_ylabel("Queue Depth")
    _save_figure(figure, path)


def save_utilization_comparison_chart(
    policy_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    """Save grouped utilization comparison by policy.

    Filename convention is caller-managed and deterministic (for example:
    ``utilization_by_policy.png``).
    """
    policies = [str(row.get("policy", "unknown")) for row in policy_rows]
    gpu_utilization = [float(row.get("gpu_utilization", 0.0)) for row in policy_rows]
    cpu_utilization = [float(row.get("cpu_utilization", 0.0)) for row in policy_rows]

    figure, axis = plt.subplots(figsize=(9, 4.5))
    if policy_rows:
        indices = list(range(len(policies)))
        width = 0.35
        gpu_positions = [index - width / 2 for index in indices]
        cpu_positions = [index + width / 2 for index in indices]
        axis.bar(gpu_positions, gpu_utilization, width, label="GPU")
        axis.bar(cpu_positions, cpu_utilization, width, label="CPU")
        axis.set_xticks(indices)
        axis.set_xticklabels(policies, rotation=20, ha="right")
        axis.legend()
    else:
        _show_empty_chart_message(axis, message="No policy summary rows to plot.")
    axis.set_title("GPU/CPU Utilization by Policy")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Utilization (0-1)")
    _save_figure(figure, path)


def save_throughput_comparison_chart(
    policy_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    """Save throughput comparison chart by policy.

    Filename convention is caller-managed and deterministic (for example:
    ``throughput_by_policy.png``).
    """
    policies = [str(row.get("policy", "unknown")) for row in policy_rows]
    throughput_rps = [float(row.get("throughput_rps", 0.0)) for row in policy_rows]

    figure, axis = plt.subplots(figsize=(9, 4.5))
    if policy_rows:
        axis.bar(policies, throughput_rps)
        axis.tick_params(axis="x", rotation=20)
    else:
        _show_empty_chart_message(axis, message="No policy summary rows to plot.")
    axis.set_title("Throughput by Policy")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Throughput (requests/second)")
    _save_figure(figure, path)


def save_dropped_requests_chart(
    policy_rows: list[dict[str, Any]],
    path: Path,
    *,
    use_rate: bool = True,
) -> None:
    """Save dropped requests chart by policy.

    By default this plots dropped request rate for easier cross-workload
    comparison. Set ``use_rate=False`` to plot absolute dropped count.
    Filename convention is caller-managed and deterministic (for example:
    ``dropped_rate_by_policy.png``).
    """
    policies = [str(row.get("policy", "unknown")) for row in policy_rows]
    value_key = "dropped_request_rate" if use_rate else "dropped_requests"
    values = [float(row.get(value_key, 0.0)) for row in policy_rows]
    y_label = "Dropped Request Rate" if use_rate else "Dropped Requests (count)"
    title = "Dropped Request Rate by Policy" if use_rate else "Dropped Requests by Policy"

    figure, axis = plt.subplots(figsize=(9, 4.5))
    if policy_rows:
        axis.bar(policies, values)
        axis.tick_params(axis="x", rotation=20)
    else:
        _show_empty_chart_message(axis, message="No policy summary rows to plot.")
    axis.set_title(title)
    axis.set_xlabel("Policy")
    axis.set_ylabel(y_label)
    _save_figure(figure, path)


def save_deadline_miss_rate_chart(
    policy_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    """Save deadline miss rate comparison chart by policy."""
    policies = [str(row.get("policy", "unknown")) for row in policy_rows]
    values = [float(row.get("deadline_miss_rate", 0.0)) for row in policy_rows]

    figure, axis = plt.subplots(figsize=(9, 4.5))
    if policy_rows:
        axis.bar(policies, values)
        axis.tick_params(axis="x", rotation=20)
    else:
        _show_empty_chart_message(axis, message="No policy summary rows to plot.")
    axis.set_title("Deadline Miss Rate by Policy")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Deadline Miss Rate")
    _save_figure(figure, path)


def save_queue_wait_comparison_chart(
    policy_rows: list[dict[str, Any]],
    path: Path,
    *,
    value_key: str = "p95_queue_wait_ms",
) -> None:
    """Save queue wait comparison chart by policy."""
    policies = [str(row.get("policy", "unknown")) for row in policy_rows]
    values = [float(row.get(value_key, 0.0)) for row in policy_rows]
    title_value = "P95" if value_key == "p95_queue_wait_ms" else "Max"

    figure, axis = plt.subplots(figsize=(9, 4.5))
    if policy_rows:
        axis.bar(policies, values)
        axis.tick_params(axis="x", rotation=20)
    else:
        _show_empty_chart_message(axis, message="No policy summary rows to plot.")
    axis.set_title(f"{title_value} Queue Wait by Policy")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Queue Wait (ms)")
    _save_figure(figure, path)
