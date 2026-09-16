from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from liquidity_scanner.alerting.detector import AlertDetector
from liquidity_scanner.alerting.notifier import AlertNotifier
from liquidity_scanner.config import Settings
from liquidity_scanner.db.models import Asset, Probe, ProbeRung, Score
from liquidity_scanner.db.session import get_session_factory
from liquidity_scanner.logging import get_logger
from liquidity_scanner.probe.engine import ProbeEngine
from liquidity_scanner.probe.jupiter import JupiterClient
from liquidity_scanner.scoring.engine import RungInput, ScoringEngine, ScoringInput

logger = get_logger(__name__)


class PipelineService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.probe_engine = ProbeEngine(settings)
        self.scoring_engine = ScoringEngine()
        self.alert_detector = AlertDetector()
        self.alert_notifier = AlertNotifier()

    async def probe_one(self, asset: Asset, jup: JupiterClient | None = None) -> bool:
        """Probe a single asset and commit immediately so the API can serve fresh data."""
        factory = get_session_factory()
        async with factory() as session:
            try:
                db_asset = await session.get(Asset, asset.mint)
                if db_asset is None:
                    return False
                result = await self.probe_engine.probe_asset(db_asset, jup=jup)
                probe = Probe(
                    mint=db_asset.mint,
                    probed_at=result.probed_at,
                    session_state=result.session_state,
                    ref_price_usd=result.ref_price_usd,
                    baseline_exec_px=result.baseline_exec_px,
                    ok=result.ok,
                    error=result.error,
                )
                session.add(probe)
                await session.flush()

                for rung in result.rungs:
                    session.add(
                        ProbeRung(
                            probe_id=probe.id,
                            direction=rung.direction,
                            notional_usd=rung.notional_usd,
                            token_qty=rung.token_qty,
                            out_usd=rung.out_usd,
                            efficiency=rung.efficiency,
                            route_labels=rung.route_labels,
                            rfq_share=rung.rfq_share,
                            no_route=rung.no_route,
                            leg1_route=rung.leg1_route,
                            leg2_route=rung.leg2_route,
                            binding_leg=rung.binding_leg,
                        )
                    )

                if result.ok:
                    mcap = None
                    score_out = self.scoring_engine.score(
                        ScoringInput(
                            rungs=[
                                RungInput(
                                    notional_usd=r.notional_usd,
                                    out_usd=r.out_usd,
                                    efficiency=r.efficiency,
                                    no_route=r.no_route,
                                    route_labels=r.route_labels,
                                    rfq_share=r.rfq_share,
                                    binding_leg=r.binding_leg,
                                )
                                for r in result.rungs
                            ],
                            mcap_usd=mcap,
                            cliff_efficiency_delta=self.settings.cliff_efficiency_delta,
                        )
                    )
                    score = Score(
                        mint=db_asset.mint,
                        computed_at=datetime.now(UTC),
                        exit_capacity_99=score_out.exit_capacity_99,
                        exit_capacity_95=score_out.exit_capacity_95,
                        exit_capacity_90=score_out.exit_capacity_90,
                        no_route_ceiling=score_out.no_route_ceiling,
                        mcap_usd=mcap,
                        mcap_exit_ratio=score_out.mcap_exit_ratio,
                        binding_leg=score_out.binding_leg,
                        cliff_detected=score_out.cliff_detected,
                        cliff_notional=score_out.cliff_notional,
                        rfq_dependence=score_out.rfq_dependence,
                        grade=score_out.grade,
                    )
                    session.add(score)

                    prev = await session.execute(
                        select(Score)
                        .where(Score.mint == db_asset.mint)
                        .order_by(Score.computed_at.desc())
                        .limit(2)
                    )
                    prev_scores = list(prev.scalars().all())
                    if len(prev_scores) > 1:
                        alerts = self.alert_detector.compare(prev_scores[1], score_out)
                        for alert in alerts:
                            session.add(alert)
                        if alerts:
                            await self.alert_notifier.notify(alerts)

                await session.commit()
                logger.info(
                    "asset_probed",
                    mint=db_asset.mint,
                    symbol=db_asset.symbol,
                    ok=result.ok,
                    rungs=len(result.rungs),
                )
                return result.ok
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.exception("probe_failed", mint=asset.mint, error=str(exc))
                return False

    async def probe_assets(self, assets: list[Asset], jup: JupiterClient | None = None) -> int:
        probed = 0
        for asset in assets:
            if await self.probe_one(asset, jup=jup):
                probed += 1
        return probed
