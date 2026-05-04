import pytest

from sage_sim.models import SimulationConfig
from sage_sim.workload import generate_synthetic_requests, load_requests_from_csv


def test_generate_workload_is_deterministic_with_seed() -> None:
    config = SimulationConfig(
        random_seed=7,
        simulation_duration_ms=5000,
        arrival_rate_per_second=8.0,
        drop_after_wait_ms=1500,
        default_gpu_runtime_ms=200,
        default_cpu_runtime_ms=350,
    )

    requests_a = generate_synthetic_requests(config, max_requests=20)
    requests_b = generate_synthetic_requests(config, max_requests=20)

    assert [item.request_id for item in requests_a] == [item.request_id for item in requests_b]
    assert [item.arrival_time_ms for item in requests_a] == [
        item.arrival_time_ms for item in requests_b
    ]
    assert [item.estimated_runtime_ms for item in requests_a] == [
        item.estimated_runtime_ms for item in requests_b
    ]


def test_generate_workload_changes_with_different_seed() -> None:
    config_a = SimulationConfig(
        random_seed=7,
        simulation_duration_ms=5000,
        arrival_rate_per_second=8.0,
        drop_after_wait_ms=1500,
        default_gpu_runtime_ms=200,
        default_cpu_runtime_ms=350,
    )
    config_b = SimulationConfig(
        random_seed=9,
        simulation_duration_ms=5000,
        arrival_rate_per_second=8.0,
        drop_after_wait_ms=1500,
        default_gpu_runtime_ms=200,
        default_cpu_runtime_ms=350,
    )

    requests_a = generate_synthetic_requests(config_a, max_requests=15)
    requests_b = generate_synthetic_requests(config_b, max_requests=15)
    assert [item.request_id for item in requests_a] != [item.request_id for item in requests_b]


def test_load_requests_from_csv_happy_path(tmp_path) -> None:
    csv_path = tmp_path / "requests.csv"
    csv_path.write_text(
        "\n".join(
            [
                "request_id,model_name,arrival_time_ms,estimated_runtime_ms,estimated_tokens,priority,requires_gpu,tenant_id,deadline_ms",
                "r1,llm-small,0,150,128,1,true,tenant-a,500",
                "r2,llm-medium,100,220,256,0,false,,",
            ]
        ),
        encoding="utf-8",
    )

    requests = load_requests_from_csv(csv_path)
    assert len(requests) == 2
    assert requests[0].request_id == "r1"
    assert requests[0].requires_gpu is True
    assert requests[1].tenant_id is None
    assert requests[1].deadline_ms is None


def test_load_requests_from_csv_missing_column(tmp_path) -> None:
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text(
        "\n".join(
            [
                "request_id,model_name,arrival_time_ms,estimated_runtime_ms,estimated_tokens,priority,requires_gpu,tenant_id",
                "r1,llm-small,0,150,128,1,true,tenant-a",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required CSV columns"):
        load_requests_from_csv(csv_path)


def test_load_requests_from_csv_malformed_row(tmp_path) -> None:
    csv_path = tmp_path / "malformed_row.csv"
    csv_path.write_text(
        "\n".join(
            [
                "request_id,model_name,arrival_time_ms,estimated_runtime_ms,estimated_tokens,priority,requires_gpu,tenant_id,deadline_ms",
                "r1,llm-small,not-int,150,128,1,true,tenant-a,500",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="arrival_time_ms"):
        load_requests_from_csv(csv_path)
