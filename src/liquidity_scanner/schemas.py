from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exit_capacity_99: float | None
    exit_capacity_95: float | None
    exit_capacity_90: float | None
    no_route_ceiling: float | None
    mcap_usd: float | None
    mcap_exit_ratio: float | None
    binding_leg: str | None
    cliff_detected: bool
    cliff_notional: float | None
    rfq_dependence: float | None
    grade: str | None
    computed_at: datetime


class AssetOut(BaseModel):
    mint: str
    symbol: str
    name: str
    kind: str
    quote_symbol: str | None
    tier: str
    latest_score: ScoreOut | None


class ProbeRungOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notional_usd: float
    out_usd: float | None
    efficiency: float | None
    route_labels: str | None
    rfq_share: float | None
    no_route: bool
    binding_leg: str | None


class AssetDetailOut(BaseModel):
    mint: str
    symbol: str
    name: str
    kind: str
    quote_mint: str | None
    quote_symbol: str | None
    pool: str | None
    tier: str
    latest_score: ScoreOut | None
    latest_rungs: list[ProbeRungOut]
    probed_at: datetime | None
    session_state: str | None


class ProbeHistoryOut(BaseModel):
    probed_at: datetime
    session_state: str
    ref_price_usd: float
    ok: bool
    score: ScoreOut | None


class ExitQuoteOut(BaseModel):
    mint: str
    notional_usd: float
    matched_notional_usd: float
    cash_usd: float | None
    efficiency: float | None
    route_labels: str | None
    binding_leg: str | None
    no_route: bool
    probed_at: datetime


class LeaderboardEntry(BaseModel):
    mint: str
    exit_capacity_95: float | None
    mcap_exit_ratio: float | None
    grade: str | None
    cliff_detected: bool
    no_route_ceiling: float | None
    computed_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mint: str
    kind: str
    detected_at: datetime
    prev_value: str | None
    new_value: str | None
    severity: str
