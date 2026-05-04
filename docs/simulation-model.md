# Simulation Model

## What Is Being Simulated

- Inference request arrivals over time
- Queueing under limited worker capacity
- Policy-based dequeue behavior
- Simulated execution duration on GPU/CPU workers
- Request completion or dropping outcomes

## What Is Not Being Simulated

- Real model execution kernels
- Real GPU memory pressure
- Network effects or batching internals at kernel level
- Multi-node/distributed orchestration

## Request Lifecycle

1. `arrival_time`: request appears in system
2. `queue_enter_time`: request enters scheduler queue
3. `start_time`: worker starts processing
4. `finish_time`: processing ends
5. optional `dropped_reason`: request dropped before completion

Requests remain in the scheduler queue until a compatible worker is available. This keeps policy decisions on the simulated backlog instead of letting a downstream resource FIFO queue decide execution order.

## Resource Model

- Fixed count of GPU workers and CPU workers
- Requests may require GPU or be eligible for CPU
- Runtime estimates drive simulated service duration

## Time Model

- Millisecond-based simulated time
- Discrete-event progression with SimPy
- No wall-clock execution dependency
- Requests that arrive before `simulation_duration_ms` are allowed to finish after that configured window; reports still use the configured window for throughput and utilization denominators.
- Queue wait time starts when a request enters the scheduler queue. A request is dropped with `wait_timeout` if it remains queued longer than `drop_after_wait_ms`.

## Random Seed Behavior

- Workload generation should be deterministic when seed is provided
- Tests should set explicit seeds
- Randomness sources should be centralized

## Limitations

- Accuracy depends on assumptions, not production traces
- Cost/utilization metrics are approximations
- Policy conclusions are directional, not definitive for production systems
- The simulator does not model GPU memory, batching internals, network latency, cache effects, or autoscaling behavior
- Batch-by-model affects queue ordering only; it does not model real batched execution speedups
