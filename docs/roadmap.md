# Roadmap

## Implemented v0.1 Scope

- Deterministic workload generation and CSV loading
- SimPy-driven simulation loop
- FIFO and SJF scheduling
- Core lifecycle timestamp tracking
- Core latency/throughput/drop/utilization/cost metrics
- CSV export and matplotlib charts
- Priority scheduler
- Deadline-aware scheduler
- Batch-by-model scheduler
- Policy-controlled dispatch under GPU/CPU contention
- Policy comparison script, summary table, and stress workload
- Deadline, queue wait, tenant, and model diagnostics
- Lightweight `sage-sim` CLI
- Portfolio case study document

## Portfolio Polish

- Keep README and docs synchronized with implementation
- Include sample output expectations for example commands
- Keep limitations explicit and easy to find
- Run `ruff check .` and `pytest` before tagging a release

## Stretch Goals

- Multi-tenant reporting cuts
- Sensitivity analysis over arrival rates and worker counts
- Additional fairness metrics and policy diagnostics
- Better synthetic workload profiles (burstiness, tenant skew)
- Configurable anti-starvation safeguards for SJF, priority, deadline, and batch-by-model policies
- Optional committed screenshots or small static report images for portfolio presentation

## Explicit Not-Yet Goals

- Real GPU instrumentation
- Production service deployment
- Cluster orchestration integration
- Reinforcement-learning-based scheduling
- Web dashboard and distributed infrastructure
