"""Resource utilization and cost estimate helpers."""


def estimate_utilization(total_busy_ms: int, workers: int, duration_ms: int) -> float:
    """Estimate utilization ratio in the range [0.0, 1.0]."""
    if workers <= 0 or duration_ms <= 0:
        return 0.0
    capacity_ms = workers * duration_ms
    return max(0.0, min(1.0, total_busy_ms / capacity_ms))


def estimate_cost(
    gpu_busy_ms: int,
    cpu_busy_ms: int,
    cost_per_gpu_ms: float,
    cost_per_cpu_ms: float,
) -> float:
    """Estimate total simulated execution cost."""
    return (gpu_busy_ms * cost_per_gpu_ms) + (cpu_busy_ms * cost_per_cpu_ms)


def estimate_cost_per_request(total_cost: float, completed_requests: int) -> float:
    """Estimate cost-per-request with divide-by-zero safety."""
    if completed_requests <= 0:
        return 0.0
    return total_cost / completed_requests
