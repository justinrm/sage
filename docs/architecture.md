# Architecture

## Project Overview

SAGE models AI inference request scheduling on limited GPU and CPU worker pools. The architecture is intentionally small and modular so policy behavior and metrics are easy to inspect.

## Simulation Pipeline

1. Load simulation config and policy settings.
2. Generate or load a request workload.
3. Feed requests into a scheduler queue as arrivals occur.
4. Dispatch queued requests only when compatible GPU/CPU capacity exists.
5. Record lifecycle events and completion outcomes.
6. Compute metrics and generate reports.

## Module Responsibilities

- `config.py`: load and validate YAML config
- `models.py`: core request/config/result data models
- `workload.py`: synthetic generation and CSV loading
- `scheduling/*`: policy-specific queue ordering
- `resources.py`: GPU/CPU worker pool abstractions
- `clock.py`: conversion helper for SimPy time values
- `simulation.py`: event loop and lifecycle orchestration
- `metrics/*`: event collection and summary formulas
- `reporting/*`: CSV export and matplotlib charts
- `examples/*`: reproducible command-line experiment entry points

## Data Flow

- Config -> workload generation/loading -> scheduler queue -> resource execution -> completed records -> metrics/report outputs.

## Scheduling Flow

- Arriving requests are enqueued by policy and remain in the policy queue while workers are busy.
- Scheduler chooses the next eligible candidate when a compatible GPU or CPU worker is available.
- Queued requests can expire if they exceed the configured queue wait threshold.
- Policy tie-breaking should be deterministic when possible.

## Metrics Flow

- Lifecycle timestamps become request-level derived fields.
- Request-level records are transformed into aggregate statistics.
- Summary tables and plots are exported to `reports/`.
- Generated report artifacts are ignored by git and can be recreated from the example scripts.

## MVP Assumptions

- Runtime and utilization are estimates, not hardware measurements.
- Request runtimes can be approximated from synthetic parameters.
- GPU/CPU capacity is fixed during a run.
- The simulator is single-process and intentionally does not model real serving infrastructure.
