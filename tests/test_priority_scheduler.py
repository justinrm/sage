from sage_sim.models import InferenceRequest
from sage_sim.scheduling.priority import PriorityScheduler


def test_priority_orders_by_descending_priority() -> None:
    scheduler = PriorityScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="low",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            priority=1,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="high",
            model_name="m",
            arrival_time_ms=1,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            priority=4,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    assert first is not None
    assert first.request_id == "high"


def test_priority_tie_breaks_by_arrival_then_enqueue_order() -> None:
    scheduler = PriorityScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="later",
            model_name="m",
            arrival_time_ms=10,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            priority=3,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            priority=3,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier-second",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            priority=3,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    third = scheduler.dequeue(current_time_ms=0)

    assert first is not None and first.request_id == "earlier"
    assert second is not None and second.request_id == "earlier-second"
    assert third is not None and third.request_id == "later"
