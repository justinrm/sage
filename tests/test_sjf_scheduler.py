from sage_sim.models import InferenceRequest
from sage_sim.scheduling.shortest_job_first import ShortestJobFirstScheduler


def test_sjf_orders_by_estimated_runtime() -> None:
    scheduler = ShortestJobFirstScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="long",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=100,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="short",
            model_name="m",
            arrival_time_ms=1,
            estimated_runtime_ms=40,
            estimated_tokens=64,
        )
    )
    first = scheduler.dequeue(current_time_ms=0)
    assert first is not None
    assert first.request_id == "short"


def test_sjf_tie_breaks_by_arrival_then_enqueue_order() -> None:
    scheduler = ShortestJobFirstScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="later",
            model_name="m",
            arrival_time_ms=10,
            estimated_runtime_ms=50,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=50,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="earlier-second",
            model_name="m",
            arrival_time_ms=5,
            estimated_runtime_ms=50,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    third = scheduler.dequeue(current_time_ms=0)

    assert first is not None and first.request_id == "earlier"
    assert second is not None and second.request_id == "earlier-second"
    assert third is not None and third.request_id == "later"
