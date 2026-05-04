"""Path helpers for deterministic report artifact outputs."""

from pathlib import Path

_REPORTS_DIR_NAME = "reports"


def project_root() -> Path:
    """Return repository root directory from package-relative location."""
    return Path(__file__).resolve().parents[3]


def ensure_reports_dir() -> Path:
    """Create and return the absolute reports directory path."""
    reports_dir = project_root() / _REPORTS_DIR_NAME
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def report_output_path(filename: str) -> Path:
    """Return absolute path for a deterministic report artifact filename."""
    return ensure_reports_dir() / filename


def relative_report_path(filename: str) -> Path:
    """Return user-friendly reports-relative path for logs/messages."""
    return Path(_REPORTS_DIR_NAME) / filename
