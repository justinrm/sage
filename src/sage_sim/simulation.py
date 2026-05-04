"""Simulation orchestration module."""

from collections.abc import Callable
from dataclasses import dataclass, field

import simpy

from sage_sim.clock import now_ms
from sage_sim.models import InferenceRequest, ResourceConfig, SimulationConfig
from sage_sim.scheduling.base import BaseScheduler
from sage_sim.scheduling.fifo import FifoScheduler


@dataclass
class SimulationResult:
    """Container for outputs from a simulation run."""

    completed: list[InferenceRequest] = field(default_factory=list)
    dropped: list[InferenceRequest] = field(default_factory=list)
    queue_depth_events: list[tuple[int, int]] = field(default_factory=list)
    simulation_duration_ms: int = 0
    total_gpu_busy_ms: int = 0
    total_cpu_busy_ms: int = 0


def _record_queue_depth(
    result: SimulationResult,
    scheduler: BaseScheduler,
    current_time_ms: int,
) -> None:
    """Capture queue depth at a simulation timestamp."""
    result.queue_depth_events.append((current_time_ms, scheduler.observe_queue_depth()))


def _drop_request(
    request: InferenceRequest,
    *,
    current_time_ms: int,
    reason: str,
    result: SimulationResult,
    scheduler: BaseScheduler,
) -> None:
    """Mark a request as dropped and record queue depth."""
    request.status = "dropped"
    request.dropped_reason = reason
    request.finish_time_ms = current_time_ms
    result.dropped.append(request)
    _record_queue_depth(result, scheduler, current_time_ms)


def _run_request(
    env: simpy.Environment,
    request: InferenceRequest,
    *,
    result: SimulationResult,
    scheduler: BaseScheduler,
    on_complete: Callable[[InferenceRequest], None],
) -> simpy.events.Event:
    """Execute one request lifecycle after policy-controlled dispatch."""
    queue_enter_time = request.queue_enter_time_ms
    if queue_enter_time is None:
        queue_enter_time = now_ms(env.now)
        request.queue_enter_time_ms = queue_enter_time

    request.status = "running"
    request.start_time_ms = now_ms(env.now)
    runtime_ms = max(1, int(request.estimated_runtime_ms))
    yield env.timeout(runtime_ms)

    request.status = "completed"
    request.finish_time_ms = now_ms(env.now)
    result.completed.append(request)
    if request.requires_gpu:
        result.total_gpu_busy_ms += runtime_ms
    else:
        result.total_cpu_busy_ms += runtime_ms
    _record_queue_depth(result, scheduler, now_ms(env.now))
    on_complete(request)


def run_simulation(
    requests: list[InferenceRequest],
    simulation_config: SimulationConfig,
    resource_config: ResourceConfig,
    scheduler: BaseScheduler | None = None,
) -> SimulationResult:
    """Run the discrete-event simulation in millisecond time units."""
    active_scheduler = scheduler if scheduler is not None else FifoScheduler()
    result = SimulationResult(simulation_duration_ms=simulation_config.simulation_duration_ms)

    env = simpy.Environment()
    eligible_requests = sorted(requests, key=lambda request: request.arrival_time_ms)
    active_gpu_workers = 0
    active_cpu_workers = 0

    def drop_expired_queued_requests() -> None:
        """Drop queued requests whose wait budget has expired."""
        current_time_ms = now_ms(env.now)
        expired_requests = active_scheduler.purge_expired(
            current_time_ms=current_time_ms,
            max_queue_wait_ms=simulation_config.drop_after_wait_ms,
        )
        for expired_request in expired_requests:
            _drop_request(
                expired_request,
                current_time_ms=current_time_ms,
                reason="wait_timeout",
                result=result,
                scheduler=active_scheduler,
            )

    def mark_worker_complete(request: InferenceRequest) -> None:
        """Release logical worker capacity and continue dispatching backlog."""
        nonlocal active_gpu_workers, active_cpu_workers
        if request.requires_gpu:
            active_gpu_workers -= 1
        else:
            active_cpu_workers -= 1
        dispatch_available_workers()

    def start_request(request: InferenceRequest) -> None:
        """Reserve logical worker capacity and start request execution."""
        nonlocal active_gpu_workers, active_cpu_workers
        if request.requires_gpu:
            active_gpu_workers += 1
        else:
            active_cpu_workers += 1
        _record_queue_depth(result, active_scheduler, now_ms(env.now))
        env.process(
            _run_request(
                env,
                request,
                result=result,
                scheduler=active_scheduler,
                on_complete=mark_worker_complete,
            )
        )

    def dispatch_available_workers() -> None:
        """Dispatch queued work while compatible worker slots are available."""
        drop_expired_queued_requests()
        made_progress = True
        while made_progress:
            made_progress = False
            while active_gpu_workers < resource_config.gpu_workers:
                next_gpu_request = active_scheduler.dequeue_for_resource(
                    current_time_ms=now_ms(env.now),
                    requires_gpu=True,
                )
                if next_gpu_request is None:
                    break
                start_request(next_gpu_request)
                made_progress = True

            while active_cpu_workers < resource_config.cpu_workers:
                next_cpu_request = active_scheduler.dequeue_for_resource(
                    current_time_ms=now_ms(env.now),
                    requires_gpu=False,
                )
                if next_cpu_request is None:
                    break
                start_request(next_cpu_request)
                made_progress = True

    def queued_timeout_process(request: InferenceRequest) -> simpy.events.Event:
        """Wake at a request's queue timeout so drops do not wait for another event."""
        yield env.timeout(simulation_config.drop_after_wait_ms)
        if request.status == "queued":
            drop_expired_queued_requests()
            dispatch_available_workers()

    def arrival_process(request: InferenceRequest) -> simpy.events.Event:
        """Wait for request arrival, then place it into the scheduler queue."""
        if request.arrival_time_ms > simulation_config.simulation_duration_ms:
            _drop_request(
                request,
                current_time_ms=simulation_config.simulation_duration_ms,
                reason="arrived_after_simulation_window",
                result=result,
                scheduler=active_scheduler,
            )
            return env.timeout(0)

        yield env.timeout(max(0, request.arrival_time_ms - now_ms(env.now)))
        request.status = "queued"
        request.queue_enter_time_ms = now_ms(env.now)
        active_scheduler.enqueue(request)
        _record_queue_depth(result, active_scheduler, now_ms(env.now))
        env.process(queued_timeout_process(request))
        dispatch_available_workers()

    for request in eligible_requests:
        env.process(arrival_process(request))

    env.run()
    return result
