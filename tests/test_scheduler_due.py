from datetime import UTC, datetime, timedelta

from liquidity_scanner.config import Settings
from liquidity_scanner.scheduler.due import is_asset_due, pick_next_due_asset, tier_refresh_interval


def test_tier_refresh_intervals():
    settings = Settings()
    assert tier_refresh_interval("A", settings) == timedelta(minutes=30)
    assert tier_refresh_interval("B", settings) == timedelta(hours=2)
    assert tier_refresh_interval("C", settings) == timedelta(hours=12)


def test_never_probed_is_due():
    settings = Settings()
    now = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    assert is_asset_due("A", None, now, settings) is True


def test_recent_probe_not_due():
    settings = Settings()
    now = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=10)
    assert is_asset_due("A", last, now, settings) is False


def test_stale_probe_is_due():
    settings = Settings()
    now = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=45)
    assert is_asset_due("A", last, now, settings) is True


def test_pick_next_due_prefers_tier_a():
    settings = Settings()
    now = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    stale = now - timedelta(hours=1)
    assets = [
        ("mint-c", "C", stale),
        ("mint-a", "A", stale),
        ("mint-b", "B", stale),
    ]
    assert pick_next_due_asset(assets, now, settings) == "mint-a"


def test_pick_next_due_skips_fresh_assets():
    settings = Settings()
    now = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    fresh = now - timedelta(minutes=5)
    stale = now - timedelta(hours=2)
    assets = [
        ("mint-a-fresh", "A", fresh),
        ("mint-b-stale", "B", stale),
    ]
    assert pick_next_due_asset(assets, now, settings) == "mint-b-stale"
