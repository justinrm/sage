"""Batch-by-model scheduler."""

from collections import defaultdict, deque

from sage_sim.models import InferenceRequest
from sage_sim.scheduling.base import BaseScheduler


class BatchByModelScheduler(BaseScheduler):
    """Group requests by model and dispatch from largest group first.

    This policy keeps the implementation intentionally small: it models model
    affinity as queue ordering only, not real kernel batching or batch sizes.
    """

    def __init__(self) -> None:
        self._queues: dict[str, deque[tuple[int, InferenceRequest]]] = defaultdict(deque)
        self._enqueue_order = 0

    def enqueue(self, request: InferenceRequest) -> None:
        self._queues[request.model_name].append((self._enqueue_order, request))
        self._enqueue_order += 1

    def dequeue(self, current_time_ms: int) -> InferenceRequest | None:
        del current_time_ms
        if not self._queues:
            return None
        return self._pop_from_largest_matching_group()

    def dequeue_for_resource(
        self,
        current_time_ms: int,
        *,
        requires_gpu: bool,
    ) -> InferenceRequest | None:
        del current_time_ms
        return self._pop_from_largest_matching_group(requires_gpu=requires_gpu)

    def has_work(self) -> bool:
        return any(self._queues.values())

    def purge_expired(
        self,
        current_time_ms: int,
        *,
        max_queue_wait_ms: int,
    ) -> list[InferenceRequest]:
        expired: list[InferenceRequest] = []
        empty_models: list[str] = []

        for model_name, queue in self._queues.items():
            active_queue: deque[tuple[int, InferenceRequest]] = deque()
            for entry in queue:
                _, request = entry
                queue_enter_time_ms = request.queue_enter_time_ms
                if (
                    queue_enter_time_ms is not None
                    and current_time_ms - queue_enter_time_ms >= max_queue_wait_ms
                ):
                    expired.append(request)
                else:
                    active_queue.append(entry)
            self._queues[model_name] = active_queue
            if not active_queue:
                empty_models.append(model_name)

        for model_name in empty_models:
            del self._queues[model_name]
        return expired

    def observe_queue_depth(self) -> int:
        return sum(len(queue) for queue in self._queues.values())

    def _pop_from_largest_matching_group(
        self,
        *,
        requires_gpu: bool | None = None,
    ) -> InferenceRequest | None:
        if not self._queues:
            return None

        # Select from the largest model queue. If group sizes tie, pick the
        # group whose oldest request arrived in queue first; then model name.
        candidates = [
            (
                model_name,
                queue,
                [
                    entry
                    for entry in queue
                    if requires_gpu is None or entry[1].requires_gpu == requires_gpu
                ],
            )
            for model_name, queue in self._queues.items()
        ]
        candidates = [item for item in candidates if item[2]]
        if not candidates:
            return None

        largest_size = max(len(matching_entries) for _, _, matching_entries in candidates)
        candidates = [
            (model_name, queue, matching_entries)
            for model_name, queue, matching_entries in candidates
            if len(matching_entries) == largest_size
        ]
        selected_model, selected_queue = min(
            candidates,
            key=lambda item: (item[2][0][0], item[0]),
        )[:2]

        picked: InferenceRequest | None = None
        for index, (_, request) in enumerate(selected_queue):
            if requires_gpu is None or request.requires_gpu == requires_gpu:
                _, picked = selected_queue[index]
                del selected_queue[index]
                break
        if not selected_queue:
            del self._queues[selected_model]
        return picked
