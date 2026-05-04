# AGENTS.md

## Project Purpose

SAGE is a Python project for simulating AI inference scheduling across limited GPU and CPU worker pools. The primary goal is portfolio-quality systems thinking and clear engineering tradeoff communication, not production deployment.

## MVP Boundaries

- Keep scope small, deterministic, and explainable
- Implement discrete-event simulation assumptions with SimPy
- Support FIFO and SJF first
- Capture lifecycle timestamps and core performance metrics
- Export simple CSV and matplotlib outputs
- Avoid real GPU integration, orchestration platforms, and distributed systems

## Python Style Expectations

- Use Python 3.11+ features and type hints
- Prefer explicit, readable code over clever abstractions
- Keep functions focused and side effects obvious
- Use dataclasses or pydantic models where appropriate
- Avoid hidden global state and hidden randomness
- Add docstrings for public APIs

## Dependency Expectations

- Runtime: `simpy`, `pandas`, `matplotlib`, `pydantic`, `pyyaml`
- Dev: `pytest`, `ruff`
- Do not add heavy dependencies unless explicitly requested

## Testing Expectations

- Use `pytest`
- Cover scheduler ordering and tie-breaking behavior
- Cover workload determinism with seeded randomness
- Cover metric formulas and empty-result edge cases
- Keep tests fast, deterministic, and independent of external services

## Documentation Expectations

- Keep docs portfolio-friendly and honest about limitations
- Explain simulation assumptions and formulas clearly
- Separate MVP goals from stretch goals
- Keep example scripts and docs synchronized with implementation

## Simulation Assumptions

- Discrete-event timing model implemented with SimPy
- Synthetic request workloads with optional CSV input
- Fixed GPU/CPU worker pool sizes
- Estimated runtime- and policy-driven scheduling behavior
- Utilization and cost are explicitly estimates

## Commands To Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
ruff format .
pytest
```
