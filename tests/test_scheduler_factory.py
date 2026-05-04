import pytest

from sage_sim.scheduling import create_scheduler
from sage_sim.scheduling.batch_by_model import BatchByModelScheduler
from sage_sim.scheduling.deadline_aware import DeadlineAwareScheduler
from sage_sim.scheduling.fifo import FifoScheduler
from sage_sim.scheduling.priority import PriorityScheduler
from sage_sim.scheduling.shortest_job_first import ShortestJobFirstScheduler


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        (None, FifoScheduler),
        ("fifo", FifoScheduler),
        ("shortest_job_first", ShortestJobFirstScheduler),
        ("sjf", ShortestJobFirstScheduler),
        ("priority", PriorityScheduler),
        ("priority_queue", PriorityScheduler),
        ("deadline_aware", DeadlineAwareScheduler),
        ("deadline", DeadlineAwareScheduler),
        ("batch_by_model", BatchByModelScheduler),
        ("batch", BatchByModelScheduler),
    ],
)
def test_create_scheduler_supports_expected_names(
    name: str | None,
    expected_type: type,
) -> None:
    scheduler = create_scheduler(name)
    assert isinstance(scheduler, expected_type)


def test_create_scheduler_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown scheduler"):
        create_scheduler("unknown-policy")
