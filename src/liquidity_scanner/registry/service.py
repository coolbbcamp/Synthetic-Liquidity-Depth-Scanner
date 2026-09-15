from __future__ import annotations

from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from liquidity_scanner.config import Settings
from liquidity_scanner.constants import XSTOCK_MINTS
from liquidity_scanner.db.models import Asset, ImpersonationFlag as ImpersonationFlagModel
from liquidity_scanner.logging import get_logger
from liquidity_scanner.registry.impersonation import ImpersonationDetector
from liquidity_scanner.registry.sources import RegistrySources

logger = get_logger(__name__)


class RegistryService:
    def __init__(self, settings: Settings, session: AsyncSession) -> None:
        self.settings = settings
        self.session = session

    async def sync(self) -> dict[str, int]:
        async with httpx.AsyncClient(headers={"User-Agent": self.settings.user_agent}) as client:
            sources = RegistrySources(self.settings, client)
            snapshot = await sources.build_snapshot()
            snapshot.generated_at = datetime.now(UTC).isoformat()

        detector = ImpersonationDetector(set(XSTOCK_MINTS.values()))
        flags = detector.detect(snapshot.assets)

        upserted = 0
        for record in snapshot.assets:
            existing = await self.session.get(Asset, record.mint)
            if existing is None:
                existing = Asset(mint=record.mint)
                self.session.add(existing)
            existing.symbol = record.symbol
            existing.name = record.name
            existing.kind = record.kind
            existing.issuer = record.issuer
            existing.listing_provider = record.listing_provider
            existing.quote_mint = record.quote_mint
            existing.quote_symbol = record.quote_symbol
            existing.pool = record.pool
            existing.decimals = record.decimals
            existing.verified_source = record.verified_source
            existing.active = record.active
            existing.first_seen = existing.first_seen or datetime.now(UTC)
            upserted += 1

        for flag in flags:
            result = await self.session.execute(
                select(ImpersonationFlagModel).where(
                    ImpersonationFlagModel.mint == flag.mint,
                    ImpersonationFlagModel.suspected_target_mint == flag.suspected_target_mint,
                    ImpersonationFlagModel.reason == flag.reason,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = ImpersonationFlagModel(
                    mint=flag.mint,
                    suspected_target_mint=flag.suspected_target_mint,
                    reason=flag.reason,
                    confidence=flag.confidence,
                    detected_at=datetime.now(UTC),
                )
                self.session.add(row)
            else:
                row.confidence = flag.confidence
                row.detected_at = datetime.now(UTC)

        await self.session.commit()
        logger.info(
            "registry_sync_complete",
            assets=upserted,
            flags=len(flags),
            source_hash=snapshot.source_hash,
            counts=snapshot.raw_counts,
        )
        return {"assets": upserted, "flags": len(flags)}
