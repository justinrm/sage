# TODO

## Milestone 1: Project Foundation

- [x] Project tree created
- [x] `pyproject.toml` created
- [x] `.cursor/rules` created
- [x] `AGENTS.md` created
- [x] `.gitignore` created
- [x] `README.md` created
- [x] Docs scaffolded
- [x] Placeholder source files created
- [x] Placeholder tests created

## Milestone 2: Workload Model

- [x] Define request model (required fields, lifecycle fields, type hints, defaults)
- [x] Define resource model (GPU/CPU worker counts and cost assumptions)
- [x] Define workload config (seed, duration, arrival rate, runtime defaults, drop threshold)
- [x] Generate synthetic requests (deterministic IDs/timestamps from seed and config)
- [x] Load requests from CSV (required columns, null handling, helpful validation errors)
- [x] Deterministic seed support (same seed => same generated workload)
- [x] Tests for workload generation and CSV loading (happy path + malformed input)

Done criteria:
- [x] `workload.py` can generate and load requests with predictable outputs.
- [x] Request records align with `docs/simulation-model.md` field expectations.
- [x] `tests/test_workload.py` covers deterministic behavior and basic validation paths.

## Milestone 3: FIFO Simulation

- [x] Implement basic SimPy environment (single run loop, ms-based time handling)
- [x] Implement FIFO scheduler end-to-end (enqueue/dequeue/queue depth observation)
- [x] Simulate request arrival (enqueue at arrival time, set queue-enter timestamp)
- [x] Simulate GPU/CPU execution (respect worker capacity and runtime assumptions)
- [x] Collect completed and dropped records (status + lifecycle timestamps)
- [x] Smoke test simulation run (small deterministic config passes)

Done criteria:
- [x] `run_simulation()` returns non-empty records for a small synthetic workload.
- [x] Queue depth events are captured during execution.
- [x] `tests/test_simulation_smoke.py` is unskipped and passing.

## Milestone 4: Metrics

- [x] Average latency (`finish - arrival` mean)
- [x] P95 latency (95th percentile of end-to-end latency)
- [x] Throughput (completed requests / simulated seconds)
- [x] Queue wait time (`start - queue_enter`)
- [x] Service time (`finish - start`)
- [x] Dropped request count and rate (`dropped / total`)
- [x] GPU/CPU utilization estimate (busy time / total capacity)
- [x] Cost estimate and cost-per-request (from utilization assumptions)
- [x] CSV export of request-level records and summary metrics

Done criteria:
- [x] Metric formulas in code match `docs/metrics.md`.
- [x] Empty-result edge cases return safe values (no crashes/divide-by-zero).
- [x] `tests/test_metrics.py` is unskipped and validates key formulas.

## Milestone 5: Policy Comparison

- [x] Shortest-job-first policy finalized (deterministic tie-breaking)
- [x] Priority queue policy finalized (documented priority and ties behavior)
- [x] Deadline-aware scheduling finalized (behavior for no-deadline requests defined)
- [x] Batch-by-model policy finalized (tie-breaking and starvation guard notes)
- [x] Compare policies on same workload seed/config (apples-to-apples runs)
- [x] Report table output (policy vs core metrics in one summary table)

Done criteria:
- [x] Each scheduler passes ordering tests (including tie behavior where applicable).
- [x] Comparison script runs FIFO/SJF at minimum on the same workload.
- [x] Output clearly shows tradeoffs, not just single-metric winners.

## Milestone 6: Charts and Reports

- [x] Latency distribution chart (clear bins/labels/title)
- [x] Queue depth over time chart (time on x-axis, depth on y-axis)
- [x] Utilization comparison chart (GPU/CPU utilization per policy)
- [x] Throughput comparison chart (requests/sec per policy)
- [x] Dropped requests chart (count or rate per policy)
- [x] Save reports to `reports/` using reproducible, relative paths

Done criteria:
- [x] At least one end-to-end run produces CSV + charts without manual file editing.
- [x] Charts include readable titles, axis labels, and deterministic filenames.
- [x] `examples/` scripts document where outputs are written.

## Milestone 7: Portfolio Polish

- [x] README screenshots or sample outputs (one baseline + one policy comparison)
- [x] Architecture docs complete (pipeline, module responsibilities, assumptions)
- [x] Scheduling docs complete (policy behavior + starvation/tradeoff discussion)
- [x] Metrics docs complete (formula definitions + interpretation guidance)
- [x] Clean examples (copy-paste runnable commands with expected outputs)
- [x] Final limitations section (explicit non-goals and assumption caveats)
- [ ] Tag `v0.1.0` after tests/lint/docs are in a stable state

Done criteria:
- [x] A reviewer can clone, run, and understand the project in < 15 minutes.
- [x] README and docs reflect actual implementation (no stale placeholders).
- [ ] Release tag is created only after a passing quality check (`ruff`, `pytest`).

## Milestone 8: Standout Case Study

- [x] Refactor simulation dispatch so scheduler policies control queued backlog under GPU/CPU contention
- [x] Add integration tests proving policies affect end-to-end simulation outcomes
- [x] Add curated stress config and CSV workload for policy tradeoff comparison
- [x] Add deadline miss, p95/max queue wait, tenant, and model diagnostics
- [x] Export stress comparison CSVs and high-signal charts
- [x] Add portfolio-friendly case study documentation
- [x] Add lightweight `sage-sim` CLI for run and compare workflows

Done criteria:
- [x] Policy comparison produces differentiated metrics on the curated stress workload.
- [x] New behavior is covered by focused tests.
- [x] Documentation describes the dispatch model, diagnostics, CLI, and case study.
