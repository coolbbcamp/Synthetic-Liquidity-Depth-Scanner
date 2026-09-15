from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

import httpx

from liquidity_scanner.config import Settings
from liquidity_scanner.constants import XSTOCK_MINTS


@dataclass
class AssetRecord:
    mint: str
    symbol: str
    name: str
    kind: str  # xstock | launch
    issuer: str | None = None
    listing_provider: str | None = None
    quote_mint: str | None = None
    quote_symbol: str | None = None
    pool: str | None = None
    decimals: int | None = None
    verified_source: str | None = None
    market_cap_usd: float | None = None
    volume_24h_usd: float | None = None
    active: bool = True


@dataclass
class RegistrySnapshot:
    assets: list[AssetRecord]
    source_hash: str
    generated_at: str
    raw_counts: dict[str, int] = field(default_factory=dict)


class RegistrySources:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.client = client

    async def fetch_pairs(self) -> list[dict[str, Any]]:
        url = f"{self.settings.stonkfun_base_url}/pairs?launchable=true"
        resp = await self.client.get(url, timeout=30.0)
        resp.raise_for_status()
        return resp.json()["data"]["pairs"]

    async def fetch_graduated_tokens(self, quote_mint: str) -> list[dict[str, Any]]:
        tokens: list[dict[str, Any]] = []
        page = 1
        while True:
            url = (
                f"{self.settings.stonkfun_base_url}/tokens"
                f"?status=graduated&quoteMint={quote_mint}&pageSize=100&page={page}"
            )
            resp = await self.client.get(url, timeout=30.0)
            resp.raise_for_status()
            batch = resp.json()["data"]["tokens"]
            if not batch:
                break
            tokens.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            if page > 20:
                break
        return tokens

    async def build_snapshot(self) -> RegistrySnapshot:
        pairs = await self.fetch_pairs()
        xstock_pairs = [p for p in pairs if p.get("category") == "xstock"]
        assets: list[AssetRecord] = []
        seen: set[str] = set()

        for symbol, mint in XSTOCK_MINTS.items():
            if mint in seen:
                continue
            seen.add(mint)
            pair = next((p for p in xstock_pairs if p["mint"] == mint), None)
            assets.append(
                AssetRecord(
                    mint=mint,
                    symbol=symbol,
                    name=pair["name"] if pair else symbol,
                    kind="xstock",
                    issuer="Backed Assets (JE) Limited (xStocks)",
                    listing_provider=None,
                    quote_mint=self.settings.usdc_mint,
                    quote_symbol="USDC",
                    decimals=pair.get("decimals") if pair else 8,
                    verified_source="pump.fun+xstocks",
                    active=True,
                )
            )

        launch_count = 0
        for pair in xstock_pairs:
            quote_mint = pair["mint"]
            quote_symbol = pair.get("symbol", "")
            graduated = await self.fetch_graduated_tokens(quote_mint)
            launch_count += len(graduated)
            for token in graduated:
                mint = token["mint"]
                if mint in seen:
                    continue
                seen.add(mint)
                market = token.get("market") or {}
                assets.append(
                    AssetRecord(
                        mint=mint,
                        symbol=token.get("symbol", ""),
                        name=token.get("name", ""),
                        kind="launch",
                        issuer=None,
                        listing_provider="StonkFun",
                        quote_mint=quote_mint,
                        quote_symbol=quote_symbol,
                        pool=token.get("pool"),
                        decimals=token.get("decimals"),
                        verified_source="stonkfun",
                        market_cap_usd=market.get("marketCapUsd"),
                        volume_24h_usd=market.get("volume24hUsd"),
                        active=True,
                    )
                )

        payload = json.dumps(
            [{"mint": a.mint, "kind": a.kind, "quote_mint": a.quote_mint} for a in assets],
            sort_keys=True,
        )
        source_hash = hashlib.sha256(payload.encode()).hexdigest()
        from datetime import UTC, datetime

        return RegistrySnapshot(
            assets=assets,
            source_hash=source_hash,
            generated_at=datetime.now(UTC).isoformat(),
            raw_counts={
                "xstock_pairs": len(xstock_pairs),
                "launches": launch_count,
                "total_assets": len(assets),
            },
        )
