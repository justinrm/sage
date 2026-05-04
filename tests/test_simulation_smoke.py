from sage_sim.models import ResourceConfig, SimulationConfig
from sage_sim.simulation import run_simulation
from sage_sim.workload import generate_synthetic_requests


def test_simulation_smoke_run() -> None:
    simulation_config = SimulationConfig(
        random_seed=7,
        simulation_duration_ms=3000,
        arrival_rate_per_second=6.0,
        drop_after_wait_ms=5000,
        default_gpu_runtime_ms=150,
        default_cpu_runtime_ms=80,
    )
    resource_config = ResourceConfig(
        gpu_workers=1,
        cpu_workers=1,
        cost_per_gpu_ms=0.001,
        cost_per_cpu_ms=0.0002,
    )
    requests = generate_synthetic_requests(simulation_config, max_requests=12)

    result = run_simulation(requests, simulation_config, resource_config)

    total_processed = len(result.completed) + len(result.dropped)
    assert total_processed > 0
    assert len(result.queue_depth_events) > 0

    for request in result.completed:
        assert request.queue_enter_time_ms is not None
        assert request.start_time_ms is not None
        assert request.finish_time_ms is not None
        assert request.status == "completed"
        assert request.start_time_ms >= request.queue_enter_time_ms
        assert request.finish_time_ms >= request.start_time_ms

    for request in result.dropped:
        assert request.status == "dropped"
        assert request.dropped_reason is not None
        assert request.finish_time_ms is not None
