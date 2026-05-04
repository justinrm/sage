from pathlib import Path

import pytest

from sage_sim.config import load_config


def test_load_baseline_config() -> None:
    config_path = Path("configs/baseline.yaml")
    config = load_config(config_path)
    assert config.simulation.random_seed == 42
    assert config.simulation.simulation_duration_ms == 60000
    assert config.resources.gpu_workers == 2
    assert config.resources.cpu_workers == 4
    assert config.scheduler is None


def test_load_config_rejects_missing_required_key(tmp_path: Path) -> None:
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text(
        "\n".join(
            [
                "random_seed: 7",
                "simulation_duration_ms: 1000",
                "arrival_rate_per_second: 1",
                "gpu_workers: 1",
                "cpu_workers: 1",
                "default_gpu_runtime_ms: 100",
                "default_cpu_runtime_ms: 200",
                "cost_per_gpu_ms: 0.00001",
                "cost_per_cpu_ms: 0.000001",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="drop_after_wait_ms"):
        load_config(bad_config)
