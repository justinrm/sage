# Scheduling Policies

## FIFO

First in, first out based on queue entry order.

- Pros: simple, predictable, fair by arrival order
- Risks: long requests can block short ones
- Tie behavior: requests that arrive together keep enqueue order

## Shortest-Job-First (SJF)

Prioritize requests with smaller estimated runtime.

- Pros: often lowers mean latency
- Risks: long jobs can starve without safeguards
- Tie behavior: `estimated_runtime_ms` then `arrival_time_ms`, then enqueue order

## Priority Queue

Prioritize higher priority requests.

- Pros: supports tenant/service tier objectives
- Risks: low-priority starvation if overloaded
- Priority semantics: higher integer `priority` value runs first
- Tie behavior: `priority` (desc), then `arrival_time_ms`, then enqueue order

## Batch by Model

Group compatible `model_name` requests for potential efficiency.

- Pros: can improve effective throughput in model-homogeneous bursts
- Risks: increased wait for minority model traffic
- Group selection: largest model group first
- Tie behavior: if groups are equal size, choose group whose oldest queued request was enqueued first, then model name
- In-group behavior: FIFO order within each model group
- Starvation guard notes: this MVP version documents starvation risk but does not apply active anti-starvation rebalancing yet

## Deadline-Aware

Prioritize requests based on time remaining before deadline.

- Pros: can reduce deadline misses
- Risks: may degrade average latency or fairness
- Deadline semantics: requests with a `deadline_ms` are always considered before no-deadline requests
- No-deadline behavior: FIFO fallback among requests that have no deadline
- Tie behavior for deadline requests: earliest `deadline_ms`, then `arrival_time_ms`, then enqueue order

## Tradeoffs

- Throughput and fairness often move in opposite directions.
- Lower mean latency can increase tail latency for some tenants.
- Strong deadline handling can amplify starvation risk.
- Batch-by-model only changes queue order in this MVP; it does not simulate real batched execution speedups.

## Starvation Risks

- SJF can repeatedly defer long-running requests.
- Priority scheduling can defer low-priority workloads.
- Deadline-first can defer non-deadline work during bursts.
- Batch-by-model can defer minority model traffic when one model dominates arrivals.
