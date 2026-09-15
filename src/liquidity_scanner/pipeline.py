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
from liquidity_scanner.scoring.engine import RungInput, ScoringEngine, ScoringInput

logger = get_logger(__name__)


class PipelineService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.probe_engine = ProbeEngine(settings)
        self.scoring_engine = ScoringEngine()
        self.alert_detector = AlertDetector()
        self.alert_notifier = AlertNotifier()

    async def probe_assets(self, assets: list[Asset]) -> int:
        factory = get_session_factory()
        probed = 0
        async with factory() as session:
            for asset in assets:
                try:
                    result = await self.probe_engine.probe_asset(asset)
                    probe = Probe(
                        mint=asset.mint,
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
                        if result.ref_price_usd and asset.kind == "launch":
                            # Use latest price * rough supply proxy unavailable; keep null unless known.
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
                            mint=asset.mint,
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
                            .where(Score.mint == asset.mint)
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

                    probed += 1
                except Exception as exc:  # noqa: BLE001
                    logger.exception("probe_failed", mint=asset.mint, error=str(exc))
            await session.commit()
        return probed
