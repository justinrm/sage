"""Randomness helpers for deterministic simulation behavior."""

from random import Random


def build_rng(seed: int) -> Random:
    """Return a seeded random generator instance."""
    return Random(seed)
