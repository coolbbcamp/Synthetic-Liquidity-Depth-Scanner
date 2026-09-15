from datetime import UTC, datetime

from liquidity_scanner.scheduler.session_state import get_session_state


def test_weekend_session_state():
    # Saturday
    assert get_session_state(datetime(2026, 9, 12, 15, 0, tzinfo=UTC)) == "weekend"
