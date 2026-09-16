from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from liquidity_scanner.config import get_settings
from liquidity_scanner.db.models import Alert, Asset, Probe, ProbeRung, Score
from liquidity_scanner.db.session import get_session, init_engine
from liquidity_scanner.logging import configure_logging, get_logger
from liquidity_scanner.schemas import (
    AlertOut,
    AssetDetailOut,
    AssetOut,
    ExitQuoteOut,
    LeaderboardEntry,
    ProbeHistoryOut,
    ProbeRungOut,
    ScoreOut,
)

configure_logging()
logger = get_logger(__name__)
settings = get_settings()
init_engine()

app = FastAPI(title="Liquidity Depth Scanner", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}


@app.get("/assets", response_model=list[AssetOut])
async def list_assets(
    kind: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[AssetOut]:
    latest_probe = (
        select(Probe.mint, func.max(Probe.probed_at).label("probed_at"))
        .where(Probe.ok.is_(True))
        .group_by(Probe.mint)
        .subquery()
    )
    stmt = (
        select(Asset, latest_probe.c.probed_at)
        .outerjoin(latest_probe, Asset.mint == latest_probe.c.mint)
        .where(Asset.active.is_(True))
    )
    if kind:
        stmt = stmt.where(Asset.kind == kind)
    result = await session.execute(stmt)
    rows = result.all()

    scores_result = await session.execute(select(Score).order_by(desc(Score.computed_at)))
    latest_score_by_mint: dict[str, Score] = {}
    for score in scores_result.scalars():
        if score.mint not in latest_score_by_mint:
            latest_score_by_mint[score.mint] = score

    out: list[AssetOut] = []
    for asset, probed_at in rows:
        score = latest_score_by_mint.get(asset.mint)
        out.append(
            AssetOut(
                mint=asset.mint,
                symbol=asset.symbol,
                name=asset.name,
                kind=asset.kind,
                quote_symbol=asset.quote_symbol,
                tier=asset.tier,
                latest_score=ScoreOut.model_validate(score) if score else None,
                probed_at=probed_at,
                is_probed=probed_at is not None,
            )
        )

    out.sort(
        key=lambda row: (
            0 if row.is_probed else 1,
            row.symbol.lower(),
            row.mint,
        )
    )
    return out


@app.get("/assets/{mint}", response_model=AssetDetailOut)
async def get_asset(mint: str, session: AsyncSession = Depends(get_session)) -> AssetDetailOut:
    asset = await session.get(Asset, mint)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")

    probe_result = await session.execute(
        select(Probe)
        .where(Probe.mint == mint, Probe.ok.is_(True))
        .options(selectinload(Probe.rungs))
        .order_by(desc(Probe.probed_at))
        .limit(1)
    )
    probe = probe_result.scalar_one_or_none()
    score_result = await session.execute(
        select(Score).where(Score.mint == mint).order_by(desc(Score.computed_at)).limit(1)
    )
    score = score_result.scalar_one_or_none()
    return AssetDetailOut(
        mint=asset.mint,
        symbol=asset.symbol,
        name=asset.name,
        kind=asset.kind,
        quote_mint=asset.quote_mint,
        quote_symbol=asset.quote_symbol,
        pool=asset.pool,
        tier=asset.tier,
        latest_score=ScoreOut.model_validate(score) if score else None,
        latest_rungs=[ProbeRungOut.model_validate(r) for r in probe.rungs] if probe else [],
        probed_at=probe.probed_at if probe else None,
        session_state=probe.session_state if probe else None,
    )


@app.get("/assets/{mint}/history", response_model=list[ProbeHistoryOut])
async def asset_history(
    mint: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ProbeHistoryOut]:
    result = await session.execute(
        select(Probe).where(Probe.mint == mint).order_by(desc(Probe.probed_at)).limit(limit)
    )
    probes = result.scalars().all()
    history: list[ProbeHistoryOut] = []
    for probe in probes:
        score_result = await session.execute(
            select(Score)
            .where(Score.mint == mint, Score.computed_at >= probe.probed_at)
            .order_by(Score.computed_at)
            .limit(1)
        )
        score = score_result.scalar_one_or_none()
        history.append(
            ProbeHistoryOut(
                probed_at=probe.probed_at,
                session_state=probe.session_state,
                ref_price_usd=probe.ref_price_usd,
                ok=probe.ok,
                score=ScoreOut.model_validate(score) if score else None,
            )
        )
    return history


@app.get("/exit-quote", response_model=ExitQuoteOut)
async def exit_quote(
    mint: str,
    notional: float = Query(gt=0),
    session: AsyncSession = Depends(get_session),
) -> ExitQuoteOut:
    """Return exit quote from the latest cached probe (no live Jupiter call)."""
    asset = await session.get(Asset, mint)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")

    probe_result = await session.execute(
        select(Probe)
        .where(Probe.mint == mint, Probe.ok.is_(True))
        .options(selectinload(Probe.rungs))
        .order_by(desc(Probe.probed_at))
        .limit(1)
    )
    probe = probe_result.scalar_one_or_none()
    if probe is None or not probe.rungs:
        raise HTTPException(status_code=404, detail="asset not probed yet")

    rungs = probe.rungs
    match = next((r for r in rungs if r.notional_usd == notional), None)
    if match is None:
        match = min(rungs, key=lambda r: abs(r.notional_usd - notional))
    return ExitQuoteOut(
        mint=mint,
        notional_usd=notional,
        matched_notional_usd=match.notional_usd,
        cash_usd=match.out_usd,
        efficiency=match.efficiency,
        route_labels=match.route_labels,
        binding_leg=match.binding_leg,
        no_route=match.no_route,
        probed_at=probe.probed_at,
    )


@app.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(
    sort: str = Query(default="mcap_exit_ratio"),
    session: AsyncSession = Depends(get_session),
) -> list[LeaderboardEntry]:
    subq = (
        select(Score)
        .distinct(Score.mint)
        .order_by(Score.mint, desc(Score.computed_at))
    )
    result = await session.execute(subq)
    scores = result.scalars().all()
    entries = [
        LeaderboardEntry(
            mint=s.mint,
            exit_capacity_95=s.exit_capacity_95,
            mcap_exit_ratio=s.mcap_exit_ratio,
            grade=s.grade,
            cliff_detected=s.cliff_detected,
            no_route_ceiling=s.no_route_ceiling,
            computed_at=s.computed_at,
        )
        for s in scores
    ]
    if sort == "exit_capacity_95":
        entries.sort(key=lambda e: e.exit_capacity_95 or 0, reverse=True)
    else:
        entries.sort(key=lambda e: e.mcap_exit_ratio or 0, reverse=True)
    return entries


@app.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[AlertOut]:
    result = await session.execute(select(Alert).order_by(desc(Alert.detected_at)).limit(limit))
    return [AlertOut.model_validate(a) for a in result.scalars().all()]
