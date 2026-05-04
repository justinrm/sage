from sage_sim.models import InferenceRequest
from sage_sim.scheduling.fifo import FifoScheduler


def test_fifo_orders_by_arrival_time() -> None:
    scheduler = FifoScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="a",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="b",
            model_name="m",
            arrival_time_ms=10,
            estimated_runtime_ms=10,
            estimated_tokens=64,
        )
    )
    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "a"
    assert second is not None and second.request_id == "b"


def test_fifo_tie_preserves_enqueue_order() -> None:
    scheduler = FifoScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="first-in",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=10,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="second-in",
            model_name="m",
            arrival_time_ms=0,
            estimated_runtime_ms=10,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "first-in"
    assert second is not None and second.request_id == "second-in"
