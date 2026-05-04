from sage_sim.models import InferenceRequest
from sage_sim.scheduling.deadline_aware import DeadlineAwareScheduler


def test_deadline_aware_prefers_deadline_requests_over_no_deadline() -> None:
    scheduler = DeadlineAwareScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="no-deadline",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            deadline_ms=None,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="deadline",
            model_name="m",
            arrival_time_ms=1,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            deadline_ms=100,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "deadline"
    assert second is not None and second.request_id == "no-deadline"


def test_deadline_aware_no_deadline_requests_fallback_to_fifo() -> None:
    scheduler = DeadlineAwareScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="first",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="second",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "first"
    assert second is not None and second.request_id == "second"


def test_deadline_aware_ties_break_by_arrival_then_enqueue_order() -> None:
    scheduler = DeadlineAwareScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="later",
            model_name="m",
            arrival_time_ms=10,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            deadline_ms=100,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            deadline_ms=100,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier-second",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=20,
            estimated_tokens=64,
            deadline_ms=100,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    third = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "earlier"
    assert second is not None and second.request_id == "earlier-second"
    assert third is not None and third.request_id == "later"
