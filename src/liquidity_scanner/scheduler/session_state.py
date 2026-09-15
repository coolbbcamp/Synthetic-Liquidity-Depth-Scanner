from __future__ import annotations

from datetime import UTC, datetime, time


def get_session_state(now: datetime | None = None) -> str:
    """Classify US equity market session for the probe timestamp (UTC input)."""
    now = now or datetime.now(UTC)
    # Approximate US market hours in UTC (simplified; no holiday calendar in v1).
    weekday = now.weekday()
    if weekday >= 5:
        return "weekend"
    t = now.time()
    if time(13, 30) <= t < time(20, 0):
        return "regular"
    if time(8, 0) <= t < time(13, 30) or time(20, 0) <= t < time(24, 0):
        return "extended"
    return "overnight"
