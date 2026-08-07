"""Clock seam.

Centralizes the "now" call so tests can monkeypatch a fixed UTC instant
without resorting to time-machine libraries.
"""
from __future__ import annotations

from datetime import UTC, datetime


def today_utc() -> datetime:
    return datetime.now(UTC)
