from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TypeVar

from liquidity_scanner.config import Settings

T = TypeVar("T")


def tier_refresh_interval(tier: str, settings: Settings) -> timedelta:
    if tier == "A":
        return timedelta(minutes=settings.tier_a_refresh_minutes)
    if tier == "B":
        return timedelta(hours=settings.tier_b_refresh_hours)
    return timedelta(hours=settings.tier_c_refresh_hours)


def is_asset_due(
    tier: str,
    last_probed: datetime | None,
    now: datetime,
    settings: Settings,
) -> bool:
    if last_probed is None:
        return True
    if last_probed.tzinfo is None:
        last_probed = last_probed.replace(tzinfo=UTC)
    return now - last_probed >= tier_refresh_interval(tier, settings)


def pick_next_due_asset(
    assets: list[tuple[T, str, datetime | None]],
    now: datetime,
    settings: Settings,
) -> T | None:
    """Pick the highest-priority asset whose refresh interval has elapsed."""
    tier_rank = {"A": 0, "B": 1, "C": 2}
    due = [
        (asset, tier, last_probed)
        for asset, tier, last_probed in assets
        if is_asset_due(tier, last_probed, now, settings)
    ]
    if not due:
        return None
    due.sort(
        key=lambda row: (
            tier_rank.get(row[1], 9),
            row[2] or datetime.min.replace(tzinfo=UTC),
        )
    )
    return due[0][0]
