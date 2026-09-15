from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import httpx

from liquidity_scanner.config import Settings
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter


@dataclass
class TokenPriceMeta:
    mint: str
    usd_price: float
    decimals: int
    liquidity: float | None = None


@dataclass
class QuoteResult:
    out_amount_raw: int
    out_amount: float
    route_labels: str
    price_impact_pct: float | None
    raw: dict[str, Any]


class JupiterClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient, limiter: TokenBucketRateLimiter) -> None:
        self.settings = settings
        self.client = client
        self.limiter = limiter
        self.credits_used = 0

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        for attempt in range(6):
            await self.limiter.acquire()
            resp = await self.client.request(method, url, **kwargs)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "2"))
                self.limiter.penalize(retry_after)
                continue
            if resp.status_code >= 500:
                await asyncio_sleep(0.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            self.credits_used += 1
            return resp
        resp.raise_for_status()
        raise RuntimeError("unreachable")

    async def get_prices(self, mints: list[str]) -> dict[str, TokenPriceMeta]:
        if not mints:
            return {}
        url = f"{self.settings.jup_api_base}/price/v3?ids={','.join(mints)}"
        resp = await self._request("GET", url, headers=self.settings.jup_headers, timeout=30.0)
        data = resp.json()
        out: dict[str, TokenPriceMeta] = {}
        for mint in mints:
            entry = data.get(mint)
            if not entry:
                continue
            out[mint] = TokenPriceMeta(
                mint=mint,
                usd_price=float(entry["usdPrice"]),
                decimals=int(entry["decimals"]),
                liquidity=entry.get("liquidity"),
            )
        return out

    async def quote(self, input_mint: str, output_mint: str, amount_raw: int) -> QuoteResult | None:
        url = (
            f"{self.settings.jup_api_base}/{self.settings.jup_quote_path}"
            f"?inputMint={input_mint}&outputMint={output_mint}"
            f"&amount={amount_raw}&slippageBps=9000"
        )
        try:
            resp = await self._request("GET", url, headers=self.settings.jup_headers, timeout=30.0)
        except httpx.HTTPError:
            return None
        data = resp.json()
        out_raw = int(data["outAmount"])
        output_decimals = 6 if output_mint == self.settings.usdc_mint else 8
        out_amount = out_raw / (10 ** output_decimals)
        labels = "+".join(step.get("swapInfo", {}).get("label", "?") for step in data.get("routePlan", []))
        impact = data.get("priceImpactPct")
        return QuoteResult(
            out_amount_raw=out_raw,
            out_amount=out_amount,
            route_labels=labels or "NO-ROUTE",
            price_impact_pct=float(impact) if impact is not None else None,
            raw=data,
        )


def raw_amount(qty: float, decimals: int) -> int:
    return int(math.floor(qty * (10 ** decimals)))


async def asyncio_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
