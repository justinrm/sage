from sage_sim.models import InferenceRequest
from sage_sim.scheduling.batch_by_model import BatchByModelScheduler


def test_batch_by_model_picks_largest_group_first() -> None:
    scheduler = BatchByModelScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="a-1",
            model_name="alpha",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="b-1",
            model_name="beta",
            arrival_time_ms=1,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="b-2",
            model_name="beta",
            arrival_time_ms=2,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    assert first is not None
    assert first.model_name == "beta"


def test_batch_by_model_tie_breaks_groups_by_oldest_enqueued_request() -> None:
    scheduler = BatchByModelScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="a-1",
            model_name="alpha",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="b-1",
            model_name="beta",
            arrival_time_ms=1,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "a-1"
    assert second is not None and second.request_id == "b-1"


def test_batch_by_model_preserves_fifo_within_model_group() -> None:
    scheduler = BatchByModelScheduler()
    scheduler.enqueue(
        InferenceRequest(
            request_id="a-1",
            model_name="alpha",
            arrival_time_ms=0,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="a-2",
            model_name="alpha",
            arrival_time_ms=1,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )
    scheduler.enqueue(
        InferenceRequest(
            request_id="b-1",
            model_name="beta",
            arrival_time_ms=2,
            estimated_runtime_ms=20,
            estimated_tokens=64,
        )
    )

    first = scheduler.dequeue(current_time_ms=0)
    second = scheduler.dequeue(current_time_ms=0)
    assert first is not None and first.request_id == "a-1"
    assert second is not None and second.request_id == "a-2"
