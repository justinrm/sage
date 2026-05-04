# Policy Tradeoff Case Study

## Question

How do simple scheduling policies change latency, deadline behavior, drops, and fairness pressure when GPU capacity is constrained?

This case study uses a curated stress workload instead of production traces. The goal is to make policy tradeoffs visible under controlled assumptions, not to predict real serving performance.

## Scenario

The workload in `data/stress_requests.csv` contains 18 requests over a short burst window. It intentionally mixes:

- long and short GPU-bound LLM requests
- CPU-bound embedding, classification, and reranking requests
- premium, standard, urgent, and batch-heavy tenants
- explicit priorities and deadlines
- repeated `llm-large` requests to exercise batch-by-model behavior

The config in `configs/stress.yaml` constrains the run to one GPU worker and one CPU worker, with an 800 ms queue wait timeout. This creates a real backlog so each policy has a chance to affect dispatch order.

## Results

Run:

```bash
python examples/compare_fifo_vs_sjf.py
```

Latest policy comparison from the stress workload:

```text
policy              avg latency  p95 latency  p95 queue wait  deadline miss  drop rate
fifo                449.5 ms     1015.0 ms    785.5 ms        85.7%          44.4%
shortest_job_first  434.3 ms      978.5 ms    672.0 ms        64.3%          22.2%
priority            455.7 ms     1083.0 ms    698.5 ms        64.3%          22.2%
deadline_aware      405.8 ms      793.0 ms    598.0 ms        78.6%          27.8%
batch_by_model      449.5 ms     1015.0 ms    785.5 ms        85.7%          44.4%
```

Generated report artifacts include:

- `reports/policy_comparison_summary.csv`
- `reports/policy_tenant_summary.csv`
- `reports/policy_model_summary.csv`
- `reports/deadline_miss_rate_by_policy.png`
- `reports/p95_queue_wait_by_policy.png`

## Interpretation

FIFO is predictable and easy to reason about, but it performs poorly in this burst because long GPU requests hold the front of the queue while short urgent work waits behind them.

Shortest-job-first improves average latency, p95 latency, queue wait pressure, and drop rate in this scenario. The tradeoff is fairness risk: long jobs can be repeatedly deferred in a sustained stream of short jobs.

Priority scheduling improves high-priority traffic and reduces drops compared with FIFO, but it does not optimize overall latency. It can also shift pain to lower-priority tenants.

Deadline-aware scheduling produces the lowest average and p95 latency here, but it does not automatically minimize deadline miss rate because some requests already have little slack by the time capacity is available.

Batch-by-model matches FIFO in this specific workload because grouping by model does not create enough benefit without modeling batch execution speedups. That is an intentional limitation: this simulator treats batch affinity as queue ordering, not real kernel batching.

## Limitations

These results are directional. The simulator does not model GPU memory, kernel batching internals, cache effects, network latency, autoscaling, or production trace variance. Cost and utilization are estimates derived from simulated busy time.

The useful takeaway is not that one policy always wins. It is that policy selection changes who waits, who misses deadlines, and which metrics improve at another metric's expense.
