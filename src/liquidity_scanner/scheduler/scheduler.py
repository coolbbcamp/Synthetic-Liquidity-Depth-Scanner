from __future__ import annotations

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from liquidity_scanner.config import Settings
from liquidity_scanner.db.models import Asset
from liquidity_scanner.db.session import get_session_factory
from liquidity_scanner.logging import get_logger
from liquidity_scanner.pipeline import PipelineService

logger = get_logger(__name__)


class ProbeScheduler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.credits_used_month = 0
        self.month_key = datetime.now(UTC).strftime("%Y-%m")

    def _check_budget(self, estimated_credits: int) -> bool:
        now_key = datetime.now(UTC).strftime("%Y-%m")
        if now_key != self.month_key:
            self.month_key = now_key
            self.credits_used_month = 0
        if self.credits_used_month + estimated_credits > self.settings.monthly_credit_budget:
            logger.warning("credit_budget_exceeded", used=self.credits_used_month, need=estimated_credits)
            return False
        self.credits_used_month += estimated_credits
        return True

    async def _run_tier(self, tier: str) -> None:
        credits_per_asset = 8
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Asset).where(Asset.active.is_(True), Asset.tier == tier))
            assets = list(result.scalars().all())
        if not assets:
            return
        estimated = len(assets) * credits_per_asset
        if not self._check_budget(estimated):
            return
        pipeline = PipelineService(self.settings)
        await pipeline.probe_assets(assets)
        logger.info("tier_probe_complete", tier=tier, assets=len(assets))

    async def sync_registry(self) -> None:
        factory = get_session_factory()
        async with factory() as session:
            from liquidity_scanner.registry.service import RegistryService

            service = RegistryService(self.settings, session)
            await service.sync()
            await self._assign_tiers(session)

    async def _assign_tiers(self, session) -> None:
        result = await session.execute(select(Asset).where(Asset.active.is_(True)))
        assets = list(result.scalars().all())
        xstocks = [a for a in assets if a.kind == "xstock"]
        launches = sorted(
            [a for a in assets if a.kind == "launch"],
            key=lambda a: (a.symbol, a.mint),
        )
        for asset in xstocks:
            asset.tier = "A"
        for idx, asset in enumerate(launches):
            if idx < 50:
                asset.tier = "A"
            elif idx < 200:
                asset.tier = "B"
            else:
                asset.tier = "C"
        await session.commit()

    def start(self) -> None:
        self.scheduler.add_job(self.sync_registry, "interval", hours=6, id="registry_sync")
        self.scheduler.add_job(self._run_tier, "interval", minutes=15, args=["A"], id="tier_a")
        self.scheduler.add_job(self._run_tier, "interval", hours=1, args=["B"], id="tier_b")
        self.scheduler.add_job(self._run_tier, "interval", hours=6, args=["C"], id="tier_c")
        self.scheduler.start()
        logger.info("scheduler_started")
