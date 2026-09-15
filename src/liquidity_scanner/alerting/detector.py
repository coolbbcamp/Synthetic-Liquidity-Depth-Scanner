from __future__ import annotations

from datetime import UTC, datetime

from liquidity_scanner.db.models import Alert, Score
from liquidity_scanner.scoring.engine import ScoringOutput


class AlertDetector:
    def compare(self, previous: Score, current: ScoringOutput) -> list[Alert]:
        alerts: list[Alert] = []
        now = datetime.now(UTC)

        if previous.exit_capacity_95 and current.exit_capacity_95:
            drop = (previous.exit_capacity_95 - current.exit_capacity_95) / previous.exit_capacity_95
            if drop >= 0.25:
                alerts.append(
                    Alert(
                        mint=previous.mint,
                        kind="exit_capacity_degraded",
                        detected_at=now,
                        prev_value=str(previous.exit_capacity_95),
                        new_value=str(current.exit_capacity_95),
                        severity="critical" if drop >= 0.5 else "warning",
                    )
                )

        if current.cliff_detected and not previous.cliff_detected:
            alerts.append(
                Alert(
                    mint=previous.mint,
                    kind="new_cliff_detected",
                    detected_at=now,
                    prev_value=str(previous.cliff_notional),
                    new_value=str(current.cliff_notional),
                    severity="critical",
                )
            )

        if previous.no_route_ceiling and current.no_route_ceiling:
            if current.no_route_ceiling < previous.no_route_ceiling:
                alerts.append(
                    Alert(
                        mint=previous.mint,
                        kind="no_route_ceiling_lowered",
                        detected_at=now,
                        prev_value=str(previous.no_route_ceiling),
                        new_value=str(current.no_route_ceiling),
                        severity="warning",
                    )
                )

        return alerts
