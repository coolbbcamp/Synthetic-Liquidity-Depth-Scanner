"""Live Jupiter API tests using free keyless api.jup.ag (1 RPS).

Run: pytest tests/test_free_jupiter_live.py -v -s
"""

import pytest

from liquidity_scanner.config import Settings
from liquidity_scanner.constants import XSTOCK_MINTS
from liquidity_scanner.probe.jupiter import JupiterClient, raw_amount
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter
import httpx

SPY_MINT = XSTOCK_MINTS["SPYx"]
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def free_settings(quote_version: str = "v1") -> Settings:
    return Settings(
        JUP_API_KEY="",
        JUP_API_BASE="https://api.jup.ag",
        JUP_QUOTE_VERSION=quote_version,
        JUP_RPS=1.0,
    )


@pytest.mark.asyncio
async def test_free_api_price_and_quote_v1():
    settings = free_settings("v1")
    limiter = TokenBucketRateLimiter(settings.jup_rps)
    async with httpx.AsyncClient() as client:
        jup = JupiterClient(settings, client, limiter)
        prices = await jup.get_prices([SPY_MINT])
        meta = prices[SPY_MINT]
        assert meta.decimals > 0
        assert meta.usd_price > 0
        raw = raw_amount(200 / meta.usd_price, meta.decimals)
        quote = await jup.quote(SPY_MINT, USDC, raw)
    assert quote is not None
    assert quote.out_amount > 0
    assert quote.route_labels != "NO-ROUTE"


@pytest.mark.asyncio
async def test_free_api_quote_v2():
    settings = free_settings("v2")
    limiter = TokenBucketRateLimiter(settings.jup_rps)
    async with httpx.AsyncClient() as client:
        jup = JupiterClient(settings, client, limiter)
        prices = await jup.get_prices([SPY_MINT])
        meta = prices[SPY_MINT]
        raw = raw_amount(10_000 / meta.usd_price, meta.decimals)
        quote = await jup.quote(SPY_MINT, USDC, raw)
    assert quote is not None
    assert quote.out_amount > 0


@pytest.mark.asyncio
async def test_spyx_100k_cash_recovery_on_free_tier():
    settings = free_settings("v1")
    limiter = TokenBucketRateLimiter(settings.jup_rps)
    async with httpx.AsyncClient() as client:
        jup = JupiterClient(settings, client, limiter)
        prices = await jup.get_prices([SPY_MINT])
        meta = prices[SPY_MINT]
        raw = raw_amount(100_000 / meta.usd_price, meta.decimals)
        quote = await jup.quote(SPY_MINT, USDC, raw)
    assert quote is not None
    recovery = quote.out_amount / 100_000
    assert recovery >= 0.95, f"SPYx $100k recovery {recovery:.2%} below 95% floor"
