"""FIFO scheduler."""

from collections import deque

from sage_sim.models import InferenceRequest
from sage_sim.scheduling.base import BaseScheduler


class FifoScheduler(BaseScheduler):
    """First-in, first-out scheduling policy."""

    def __init__(self) -> None:
        self._queue: deque[InferenceRequest] = deque()

    def enqueue(self, request: InferenceRequest) -> None:
        self._queue.append(request)

    def dequeue(self, current_time_ms: int) -> InferenceRequest | None:
        del current_time_ms
        if not self._queue:
            return None
        return self._queue.popleft()

    def dequeue_for_resource(
        self,
        current_time_ms: int,
        *,
        requires_gpu: bool,
    ) -> InferenceRequest | None:
        del current_time_ms
        for index, request in enumerate(self._queue):
            if request.requires_gpu == requires_gpu:
                del self._queue[index]
                return request
        return None

    def has_work(self) -> bool:
        return bool(self._queue)

    def purge_expired(
        self,
        current_time_ms: int,
        *,
        max_queue_wait_ms: int,
    ) -> list[InferenceRequest]:
        active_queue: deque[InferenceRequest] = deque()
        expired: list[InferenceRequest] = []
        for request in self._queue:
            queue_enter_time_ms = request.queue_enter_time_ms
            if (
                queue_enter_time_ms is not None
                and current_time_ms - queue_enter_time_ms >= max_queue_wait_ms
            ):
                expired.append(request)
            else:
                active_queue.append(request)
        self._queue = active_queue
        return expired

    def observe_queue_depth(self) -> int:
        return len(self._queue)
