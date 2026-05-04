"""GPU/CPU resource pool modeling utilities."""

from dataclasses import dataclass

import simpy

from sage_sim.models import ResourceConfig


@dataclass(slots=True)
class ResourcePool:
    """SimPy-backed GPU/CPU worker resources."""

    gpu: simpy.Resource
    cpu: simpy.Resource

    @property
    def gpu_workers(self) -> int:
        """Return configured GPU worker capacity."""
        return self.gpu.capacity

    @property
    def cpu_workers(self) -> int:
        """Return configured CPU worker capacity."""
        return self.cpu.capacity

    def total_workers(self) -> int:
        """Return total worker capacity."""
        return self.gpu_workers + self.cpu_workers


def build_resource_pool(env: simpy.Environment, config: ResourceConfig) -> ResourcePool:
    """Create SimPy resources from resource configuration."""
    return ResourcePool(
        gpu=simpy.Resource(env, capacity=config.gpu_workers),
        cpu=simpy.Resource(env, capacity=config.cpu_workers),
    )
