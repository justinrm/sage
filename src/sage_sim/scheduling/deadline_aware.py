"""Deadline-aware scheduler."""

from collections import deque

from sage_sim.models import InferenceRequest
from sage_sim.scheduling.base import BaseScheduler


class DeadlineAwareScheduler(BaseScheduler):
    """Pick the request with least remaining time to deadline.

    Requests with deadlines are always prioritized over requests without
    deadlines. Among no-deadline requests, ordering falls back to FIFO.
    """

    def __init__(self) -> None:
        self._with_deadline: list[tuple[int, InferenceRequest]] = []
        self._without_deadline: deque[tuple[int, InferenceRequest]] = deque()
        self._enqueue_order = 0

    def enqueue(self, request: InferenceRequest) -> None:
        entry = (self._enqueue_order, request)
        self._enqueue_order += 1
        if request.deadline_ms is None:
            self._without_deadline.append(entry)
            return
        self._with_deadline.append(entry)

    def dequeue(self, current_time_ms: int) -> InferenceRequest | None:
        del current_time_ms
        if not self.has_work():
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
        return bool(self._with_deadline or self._without_deadline)

    def purge_expired(
        self,
        current_time_ms: int,
        *,
        max_queue_wait_ms: int,
    ) -> list[InferenceRequest]:
        active_with_deadline: list[tuple[int, InferenceRequest]] = []
        active_without_deadline: deque[tuple[int, InferenceRequest]] = deque()
        expired: list[InferenceRequest] = []

        for entry in self._with_deadline:
            _, request = entry
            if _is_expired(request, current_time_ms, max_queue_wait_ms):
                expired.append(request)
            else:
                active_with_deadline.append(entry)
        for entry in self._without_deadline:
            _, request = entry
            if _is_expired(request, current_time_ms, max_queue_wait_ms):
                expired.append(request)
            else:
                active_without_deadline.append(entry)

        self._with_deadline = active_with_deadline
        self._without_deadline = active_without_deadline
        return expired

    def observe_queue_depth(self) -> int:
        return len(self._with_deadline) + len(self._without_deadline)

    def _pop_best_matching(self, *, requires_gpu: bool | None = None) -> InferenceRequest | None:
        deadline_candidates = [
            (index, entry)
            for index, entry in enumerate(self._with_deadline)
            if requires_gpu is None or entry[1].requires_gpu == requires_gpu
        ]
        if deadline_candidates:
            best_index, _ = min(
                deadline_candidates,
                key=lambda item: (
                    item[1][1].deadline_ms,
                    item[1][1].arrival_time_ms,
                    item[1][0],
                    item[1][1].request_id,
                ),
            )
            _, request = self._with_deadline.pop(best_index)
            return request

        for index, (_, request) in enumerate(self._without_deadline):
            if requires_gpu is None or request.requires_gpu == requires_gpu:
                del self._without_deadline[index]
                return request
        return None


def _is_expired(request: InferenceRequest, current_time_ms: int, max_queue_wait_ms: int) -> bool:
    queue_enter_time_ms = request.queue_enter_time_ms
    return (
        queue_enter_time_ms is not None
        and current_time_ms - queue_enter_time_ms >= max_queue_wait_ms
    )
