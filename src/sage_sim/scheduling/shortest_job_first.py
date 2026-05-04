"""Shortest-job-first scheduler."""

from sage_sim.models import InferenceRequest
from sage_sim.scheduling.base import BaseScheduler


class ShortestJobFirstScheduler(BaseScheduler):
    """Pick request with shortest estimated runtime."""

    def __init__(self) -> None:
        self._queue: list[tuple[int, InferenceRequest]] = []
        self._enqueue_order = 0

    def enqueue(self, request: InferenceRequest) -> None:
        self._queue.append((self._enqueue_order, request))
        self._enqueue_order += 1

    def dequeue(self, current_time_ms: int) -> InferenceRequest | None:
        del current_time_ms
        if not self._queue:
            return None
        return self._pop_best_matching()

    def dequeue_for_resource(
        self,
        current_time_ms: int,
        *,
        requires_gpu: bool,
    ) -> InferenceRequest | None:
        del current_time_ms
        return self._pop_best_matching(requires_gpu=requires_gpu)

    def has_work(self) -> bool:
        return bool(self._queue)

    def purge_expired(
        self,
        current_time_ms: int,
        *,
        max_queue_wait_ms: int,
    ) -> list[InferenceRequest]:
        active_queue: list[tuple[int, InferenceRequest]] = []
        expired: list[InferenceRequest] = []
        for entry in self._queue:
            _, request = entry
            queue_enter_time_ms = request.queue_enter_time_ms
            if (
                queue_enter_time_ms is not None
                and current_time_ms - queue_enter_time_ms >= max_queue_wait_ms
            ):
                expired.append(request)
            else:
                active_queue.append(entry)
        self._queue = active_queue
        return expired

    def observe_queue_depth(self) -> int:
        return len(self._queue)

    def _pop_best_matching(self, *, requires_gpu: bool | None = None) -> InferenceRequest | None:
        candidates = [
            (index, entry)
            for index, entry in enumerate(self._queue)
            if requires_gpu is None or entry[1].requires_gpu == requires_gpu
        ]
        if not candidates:
            return None

        best_index, _ = min(
            candidates,
            key=lambda item: (
                item[1][1].estimated_runtime_ms,
                item[1][1].arrival_time_ms,
                item[1][0],
                item[1][1].request_id,
            ),
        )
        _, request = self._queue.pop(best_index)
        return request
