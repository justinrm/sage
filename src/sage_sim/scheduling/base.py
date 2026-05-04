"""Base interface for scheduling policies."""

from abc import ABC, abstractmethod

from sage_sim.models import InferenceRequest


class BaseScheduler(ABC):
    """Abstract scheduler contract for queue policies."""

    @abstractmethod
    def enqueue(self, request: InferenceRequest) -> None:
        """Insert a request into the scheduling queue."""

    @abstractmethod
    def dequeue(self, current_time_ms: int) -> InferenceRequest | None:
        """Return next request to run, or None if queue is empty."""

    @abstractmethod
    def has_work(self) -> bool:
        """Return whether queued work is available."""

    @abstractmethod
    def dequeue_for_resource(
        self,
        current_time_ms: int,
        *,
        requires_gpu: bool,
    ) -> InferenceRequest | None:
        """Return next request eligible for the requested worker pool."""

    @abstractmethod
    def purge_expired(
        self,
        current_time_ms: int,
        *,
        max_queue_wait_ms: int,
    ) -> list[InferenceRequest]:
        """Remove queued requests that have exceeded the queue wait limit."""

    def observe_queue_depth(self) -> int:
        """Return queue depth if policy tracks it explicitly."""
        return 0
