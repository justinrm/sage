"""Collect raw simulation events and completed records."""

from dataclasses import dataclass, field

from sage_sim.models import InferenceRequest


@dataclass
class MetricsCollector:
    """Container for raw events that can be used by future simulations."""

    completed_requests: list[InferenceRequest] = field(default_factory=list)
    dropped_requests: list[InferenceRequest] = field(default_factory=list)
    queue_depth_events: list[tuple[int, int]] = field(default_factory=list)

    def record_queue_depth(self, time_ms: int, depth: int) -> None:
        """Track queue depth snapshots over simulation time."""
        self.queue_depth_events.append((time_ms, depth))
