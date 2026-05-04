"""Simulation clock utilities."""


def now_ms(sim_time: float) -> int:
    """Convert a SimPy clock value to integer milliseconds."""
    return int(sim_time)
