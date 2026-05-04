"""CSV export helpers."""

from pathlib import Path
from typing import Any

import pandas as pd

from sage_sim.models import InferenceRequest


def export_records_to_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Export list-of-dicts records to CSV."""
    frame = pd.DataFrame(records)
    frame.to_csv(path, index=False)


def request_to_record(request: InferenceRequest) -> dict[str, Any]:
    """Serialize one request to a CSV-friendly record."""
    return {
        "request_id": request.request_id,
        "model_name": request.model_name,
        "arrival_time_ms": request.arrival_time_ms,
        "estimated_runtime_ms": request.estimated_runtime_ms,
        "estimated_tokens": request.estimated_tokens,
        "priority": request.priority,
        "requires_gpu": request.requires_gpu,
        "tenant_id": request.tenant_id,
        "deadline_ms": request.deadline_ms,
        "status": request.status,
        "queue_enter_time_ms": request.queue_enter_time_ms,
        "start_time_ms": request.start_time_ms,
        "finish_time_ms": request.finish_time_ms,
        "dropped_reason": request.dropped_reason,
    }


def export_requests_to_csv(requests: list[InferenceRequest], path: Path) -> None:
    """Export request lifecycle records to CSV."""
    records = [request_to_record(request) for request in requests]
    export_records_to_csv(records=records, path=path)


def export_summary_to_csv(summary: dict[str, Any], path: Path) -> None:
    """Export one summary metrics row to CSV."""
    export_records_to_csv(records=[summary], path=path)
