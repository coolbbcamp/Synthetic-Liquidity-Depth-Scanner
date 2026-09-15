import os

import pytest

from liquidity_scanner.config import Settings
from liquidity_scanner.probe.jupiter import JupiterClient
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter
import httpx


@pytest.mark.skipif(not os.getenv("JUP_API_KEY"), reason="JUP_API_KEY not set")
@pytest.mark.asyncio
async def test_live_spyx_micro_quote():
    settings = Settings(JUP_API_KEY=os.environ["JUP_API_KEY"])
    limiter = TokenBucketRateLimiter(settings.jup_rps)
    async with httpx.AsyncClient() as client:
        jup = JupiterClient(settings, client, limiter)
        prices = await jup.get_prices(["XsoCS1TfEyfFhfvj8EtZ528L3CaKBDBRqRapnBbDF2W"])
        meta = prices["XsoCS1TfEyfFhfvj8EtZ528L3CaKBDBRqRapnBbDF2W"]
        qty = 200 / meta.usd_price
        raw = int(qty * (10 ** meta.decimals))
        quote = await jup.quote(
            "XsoCS1TfEyfFhfvj8EtZ528L3CaKBDBRqRapnBbDF2W",
            settings.usdc_mint,
            raw,
        )
    assert quote is not None
    assert quote.out_amount > 0
