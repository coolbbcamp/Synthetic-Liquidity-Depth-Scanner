from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select

from liquidity_scanner.config import Settings
from liquidity_scanner.db.models import Asset, Probe
from liquidity_scanner.db.session import get_session_factory
from liquidity_scanner.logging import get_logger
from liquidity_scanner.pipeline import PipelineService
from liquidity_scanner.probe.session import JupiterProbeSession
from liquidity_scanner.scheduler.due import pick_next_due_asset

logger = get_logger(__name__)


class ProbeScheduler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._probe_task: asyncio.Task | None = None
        self.credits_used_month = 0
        self.month_key = datetime.now(UTC).strftime("%Y-%m")

    async def _load_assets_with_last_probe(self) -> list[tuple[Asset, datetime | None]]:
        latest_probe = (
            select(Probe.mint, func.max(Probe.probed_at).label("last_probed"))
            .group_by(Probe.mint)
            .subquery()
        )
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(Asset, latest_probe.c.last_probed)
                .outerjoin(latest_probe, Asset.mint == latest_probe.c.mint)
                .where(Asset.active.is_(True))
            )
            return [(asset, last_probed) for asset, last_probed in result.all()]

    async def _next_due_asset(self) -> Asset | None:
        rows = await self._load_assets_with_last_probe()
        now = datetime.now(UTC)
        candidates = [(asset, asset.tier, last_probed) for asset, last_probed in rows]
        mint = pick_next_due_asset(candidates, now, self.settings)
        return mint

    async def _probe_loop(self) -> None:
        """Continuously probe one due asset at a time, respecting the shared 1 RPS limit."""
        pipeline = PipelineService(self.settings)
        async with JupiterProbeSession(self.settings) as session:
            jup = session.jupiter()
            while True:
                try:
                    asset = await self._next_due_asset()
                    if asset is None:
                        await asyncio.sleep(self.settings.probe_poll_seconds)
                        continue
                    await pipeline.probe_one(asset, jup=jup)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.exception("probe_loop_error", error=str(exc))
                    await asyncio.sleep(self.settings.probe_poll_seconds)

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
        max_a = self.settings.max_tier_a_launches
        for idx, asset in enumerate(launches):
            if idx < max_a:
                asset.tier = "A"
            elif idx < max_a + 50:
                asset.tier = "B"
            else:
                asset.tier = "C"
        await session.commit()

    def start(self) -> None:
        self.scheduler.add_job(self.sync_registry, "interval", hours=6, id="registry_sync")
        self.scheduler.start()
        self._probe_task = asyncio.create_task(self._probe_loop(), name="probe_loop")
        logger.info(
            "scheduler_started",
            jup_rps=self.settings.jup_rps,
            quote_samples=self.settings.quote_samples,
            tier_a_minutes=self.settings.tier_a_refresh_minutes,
        )

    async def stop(self) -> None:
        if self._probe_task is not None:
            self._probe_task.cancel()
            try:
                await self._probe_task
            except asyncio.CancelledError:
                pass
        self.scheduler.shutdown(wait=False)
