# SAGE

SAGE is a Python simulation project for exploring AI inference scheduling behavior across constrained GPU and CPU worker pools. It is intentionally a learning and portfolio project: the focus is on clear assumptions, reproducible experiments, and interpretable metrics rather than production-grade serving infrastructure.

The project name is SAGE. The installable package is `sage-sim`, and Python imports use `sage_sim`.

## Why This Project Exists

This project demonstrates systems thinking around queueing and scheduling tradeoffs in AI inference workloads. It shows how policy choices can affect latency, throughput, resource utilization, dropped requests, and estimated cost under controlled simulation assumptions.

## What It Simulates

- Synthetic or CSV-driven inference request streams
- Queueing behavior under fixed GPU/CPU worker capacity
- Policy-driven request selection and dispatch
- Request lifecycle timestamps from arrival to completion or drop
- CSV summaries and matplotlib charts for policy comparison

## Implemented Scheduling Policies

- FIFO: simple arrival-order scheduling
- Shortest-job-first (SJF): favors lower estimated runtime
- Priority queue: favors higher integer priority
- Deadline-aware: favors requests with earlier deadlines, with FIFO fallback for no-deadline work
- Batch by model: favors the largest queued model group, with deterministic ties

See `docs/scheduling-policies.md` for behavior, tie-breaking, and starvation risks.

## Implemented Metrics

- Average latency and p95 latency
- Throughput in completed requests per second
- Queue wait time and service time
- Queue depth over time
- Deadline miss rate
- P95 and max queue wait pressure
- Tenant-level and model-level diagnostic summaries
- GPU and CPU utilization estimates
- Dropped request count and drop rate
- Estimated total cost and cost per completed request

See `docs/metrics.md` for formulas and interpretation notes.

## Scope And Non-Goals

SAGE models scheduling behavior, not production infrastructure. It uses SimPy for discrete-event timing and keeps all workers, queues, and reports in-process.

Non-goals:

- Real GPU control, monitoring, or model execution
- Real model serving
- Distributed simulation
- Kubernetes, Ray, Celery, or cloud orchestration
- Production dashboards or deployment automation

## Project Structure

```text
sage/
  configs/         # YAML experiment and scheduler configs
  data/            # Sample CSV request data
  docs/            # Architecture, modeling, metrics, policies, roadmap
  examples/        # Runnable experiment scripts
  reports/         # Generated charts and CSV outputs
  src/             # Package source code
  tests/           # Pytest suite
```

## Quickstart

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run `ruff format .` when you intentionally want to rewrite files using the project formatter.

## Example Experiments

Run commands from the repository root after installing the package in editable mode.

```bash
python examples/run_baseline.py
python examples/compare_fifo_vs_sjf.py
```

`run_baseline.py` runs the baseline config, prints the active scheduler, and writes:

- `reports/baseline_requests.csv`
- `reports/baseline_summary.csv`
- `reports/latency_distribution_baseline.png`
- `reports/queue_depth_baseline.png`

`compare_fifo_vs_sjf.py` keeps its original filename but compares all implemented policies on the curated stress workload in `data/stress_requests.csv`. It prints a policy summary table and writes:

- `reports/policy_comparison_summary.csv`
- `reports/policy_tenant_summary.csv`
- `reports/policy_model_summary.csv`
- `reports/utilization_by_policy.png`
- `reports/throughput_by_policy.png`
- `reports/dropped_rate_by_policy.png`
- `reports/deadline_miss_rate_by_policy.png`
- `reports/p95_queue_wait_by_policy.png`
- `reports/latency_distribution_fifo.png`

Generated report files are intentionally ignored by git so every reviewer can recreate them locally.

## CLI

After installing the package, you can also run experiments through the lightweight CLI:

```bash
sage-sim run configs/baseline.yaml
sage-sim compare configs/stress.yaml --requests-csv data/stress_requests.csv
```

The CLI writes deterministic CSV and PNG artifacts to `reports/`.

## Configuration

Configs are flat YAML files under `configs/`. Required fields are:

- `random_seed`
- `simulation_duration_ms`
- `arrival_rate_per_second`
- `gpu_workers`
- `cpu_workers`
- `default_gpu_runtime_ms`
- `default_cpu_runtime_ms`
- `drop_after_wait_ms`
- `cost_per_gpu_ms`
- `cost_per_cpu_ms`

The optional `scheduler` field accepts `fifo`, `shortest_job_first`, `priority`, `deadline_aware`, or `batch_by_model`. If omitted, examples default to FIFO.

## Documentation Map

- `docs/architecture.md`: module responsibilities and data flow
- `docs/simulation-model.md`: simulation assumptions and request lifecycle
- `docs/scheduling-policies.md`: policy behavior and tradeoffs
- `docs/metrics.md`: formulas, caveats, and interpretation guidance
- `docs/case-study.md`: curated stress workload results and interpretation
- `docs/roadmap.md`: implemented scope and possible future work
- `data/README.md`: CSV workload format

## What I Learned

- Scheduling policy changes can improve one metric while making another worse. SJF can reduce average latency, but it carries a starvation risk for long-running requests.
- Deterministic seeds and explicit tie-breakers make policy comparisons easier to trust because the workload and ordering rules are reproducible.
- Policy comparisons are only meaningful when the scheduler owns a real backlog. Dispatch must happen when compatible GPU/CPU capacity is available, not when requests merely enter a downstream FIFO resource queue.
- Utilization and cost are useful for comparing scenarios, but they are estimates from the simulation model, not hardware measurements.
- Clear documentation matters as much as the implementation for a portfolio systems project: reviewers need to see assumptions, limitations, and tradeoffs quickly.
