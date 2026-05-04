# Metrics

All metrics are computed from simulated request lifecycle records. Unless stated otherwise, times are in milliseconds.

The reporting window is `simulation_duration_ms` from the run config. Requests that arrive inside that window are allowed to finish after the final arrival time, but throughput, utilization, and cost comparisons still use the configured window for a stable denominator.

## Average Latency

`average_latency_ms = mean(end_to_end_latency_ms)`

Where:

`end_to_end_latency_ms = finish_time - arrival_time`

## P95 Latency

`p95_latency_ms = percentile(end_to_end_latency_ms, 95)`

## Throughput

`throughput_rps = completed_requests / simulation_duration_seconds`

## Queue Wait Time

`queue_wait_ms = start_time - queue_enter_time`

SAGE also reports `p95_queue_wait_ms` and `max_queue_wait_ms` to expose starvation pressure under contention.

## Service Time

`service_time_ms = finish_time - start_time`

## Dropped Request Rate

`dropped_request_rate = dropped_requests / total_requests`

## Deadline Miss Rate

`deadline_miss_rate = deadline_misses / requests_with_deadlines`

A completed request misses its deadline when `finish_time_ms > deadline_ms`. A dropped request with a deadline is also counted as a deadline miss.

## Tenant And Model Diagnostics

Policy comparisons can export tenant-level and model-level summaries. These cuts reuse the same latency, queue wait, dropped request, and deadline formulas as aggregate summaries.

## GPU Utilization Estimate

`gpu_utilization = total_gpu_busy_ms / (gpu_workers * simulation_duration_ms)`

## CPU Utilization Estimate

`cpu_utilization = total_cpu_busy_ms / (cpu_workers * simulation_duration_ms)`

Utilization is capped to the range `[0.0, 1.0]` in code. A value near `1.0` means the simulated worker pool was saturated for most of the reporting window; it does not prove that real hardware would be saturated.

## Cost Per Request Estimate

`estimated_total_cost = (gpu_busy_ms * cost_per_gpu_ms) + (cpu_busy_ms * cost_per_cpu_ms)`

`cost_per_request = estimated_total_cost / completed_requests`

## Notes

- Utilization and cost values are estimates derived from simulated assumptions.
- Empty completed-result sets should return safe defaults (for example, `0` or `None`) rather than throwing unhandled errors.
- Compare policies on the same seed and config. Changing arrival rate, runtime assumptions, or worker counts changes the workload shape and makes policy-level conclusions less direct.
- Lower average latency is not always a clear win. Check p95 latency, dropped requests, and utilization to understand whether one request class improved at the expense of another.
- Cost per request is most useful for relative comparisons within this simulator. It is not a cloud bill estimate.
- Tenant and model summaries are diagnostic cuts, not fairness guarantees.
