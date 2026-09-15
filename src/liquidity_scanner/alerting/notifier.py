from __future__ import annotations

import json

import httpx

from liquidity_scanner.db.models import Alert
from liquidity_scanner.logging import get_logger

logger = get_logger(__name__)


class AlertNotifier:
    """Delivers alerts to a webhook endpoint when configured."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    async def notify(self, alerts: list[Alert]) -> None:
        for alert in alerts:
            payload = {
                "mint": alert.mint,
                "kind": alert.kind,
                "severity": alert.severity,
                "prev_value": alert.prev_value,
                "new_value": alert.new_value,
                "detected_at": alert.detected_at.isoformat(),
            }
            logger.warning("alert_emitted", **payload)
            if not self.webhook_url:
                continue
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        self.webhook_url,
                        content=json.dumps(payload),
                        headers={"Content-Type": "application/json"},
                    )
            except Exception as exc:  # noqa: BLE001
                logger.exception("alert_delivery_failed", error=str(exc))
