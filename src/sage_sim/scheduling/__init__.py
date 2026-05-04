"""Scheduling policy implementations and scheduler factory helpers."""

from collections.abc import Callable

from sage_sim.scheduling.base import BaseScheduler
from sage_sim.scheduling.batch_by_model import BatchByModelScheduler
from sage_sim.scheduling.deadline_aware import DeadlineAwareScheduler
from sage_sim.scheduling.fifo import FifoScheduler
from sage_sim.scheduling.priority import PriorityScheduler
from sage_sim.scheduling.shortest_job_first import ShortestJobFirstScheduler

_DEFAULT_SCHEDULER_NAME = "fifo"
_SCHEDULER_FACTORIES: dict[str, Callable[[], BaseScheduler]] = {
    "fifo": FifoScheduler,
    "shortest_job_first": ShortestJobFirstScheduler,
    "sjf": ShortestJobFirstScheduler,
    "priority": PriorityScheduler,
    "priority_queue": PriorityScheduler,
    "deadline_aware": DeadlineAwareScheduler,
    "deadline": DeadlineAwareScheduler,
    "batch_by_model": BatchByModelScheduler,
    "batch": BatchByModelScheduler,
}


def _normalize_scheduler_name(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def create_scheduler(name: str | None) -> BaseScheduler:
    """Create scheduler instance from optional scheduler name."""
    normalized_name = _DEFAULT_SCHEDULER_NAME if name is None else _normalize_scheduler_name(name)
    scheduler_factory = _SCHEDULER_FACTORIES.get(normalized_name)
    if scheduler_factory is None:
        options = ", ".join(sorted(_SCHEDULER_FACTORIES))
        msg = f"Unknown scheduler '{name}'. Supported scheduler names: {options}"
        raise ValueError(msg)
    return scheduler_factory()


def canonical_scheduler_name(name: str | None) -> str:
    """Return canonical scheduler name for reporting."""
    normalized_name = _DEFAULT_SCHEDULER_NAME if name is None else _normalize_scheduler_name(name)
    alias_to_canonical = {
        "fifo": "fifo",
        "shortest_job_first": "shortest_job_first",
        "sjf": "shortest_job_first",
        "priority": "priority",
        "priority_queue": "priority",
        "deadline_aware": "deadline_aware",
        "deadline": "deadline_aware",
        "batch_by_model": "batch_by_model",
        "batch": "batch_by_model",
    }
    canonical = alias_to_canonical.get(normalized_name)
    if canonical is None:
        options = ", ".join(sorted(_SCHEDULER_FACTORIES))
        msg = f"Unknown scheduler '{name}'. Supported scheduler names: {options}"
        raise ValueError(msg)
    return canonical


__all__ = [
    "BaseScheduler",
    "BatchByModelScheduler",
    "DeadlineAwareScheduler",
    "FifoScheduler",
    "PriorityScheduler",
    "ShortestJobFirstScheduler",
    "canonical_scheduler_name",
    "create_scheduler",
]
