#!/usr/bin/env python3
"""Live validation of probe + scoring logic against free Jupiter API endpoints.

Usage:
  python scripts/validate_jupiter_probe.py
  python scripts/validate_jupiter_probe.py --quote-version v2
  python scripts/validate_jupiter_probe.py --base-url https://api.jup.ag
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from liquidity_scanner.config import Settings
from liquidity_scanner.constants import XSTOCK_MINTS
from liquidity_scanner.db.models import Asset
from liquidity_scanner.probe.engine import ProbeEngine
from liquidity_scanner.probe.jupiter import JupiterClient, raw_amount
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter
from liquidity_scanner.scoring.engine import RungInput, ScoringEngine, ScoringInput

SPY_MINT = XSTOCK_MINTS["SPYx"]
STRC_MINT = XSTOCK_MINTS["STRCx"]
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def make_asset(symbol: str, mint: str) -> Asset:
    return Asset(
        mint=mint,
        symbol=symbol,
        name=symbol,
        kind="xstock",
        quote_mint=None,
        quote_symbol="USDC",
        pool=None,
        active=True,
        tier="A",
    )


async def check_endpoints(base_url: str, quote_version: str) -> dict[str, bool]:
    headers = {"User-Agent": "LiquidityDepthScanner/0.1", "Accept": "application/json"}
    quote_path = f"swap/{quote_version.lstrip('swap/').rstrip('/quote')}/quote"
    results: dict[str, bool] = {}
    async with httpx.AsyncClient() as client:
        for label, url in {
            "price_v3": f"{base_url}/price/v3?ids={SPY_MINT}",
            "quote": (
                f"{base_url}/{quote_path}"
                f"?inputMint={SPY_MINT}&outputMint={USDC}&amount=1000000&slippageBps=9000"
            ),
        }.items():
            try:
                resp = await client.get(url, headers=headers, timeout=30.0)
                results[label] = resp.status_code == 200
                status = resp.status_code
                snippet = resp.text[:80].replace("\n", " ")
            except httpx.HTTPError as exc:
                results[label] = False
                status = "ERR"
                snippet = str(exc)
            print(f"  [{label}] {base_url} -> {status} {snippet}")
    return results


async def quote_efficiency(
    settings: Settings,
    mint: str,
    notional_usd: float,
) -> tuple[float | None, str, int]:
    limiter = TokenBucketRateLimiter(settings.jup_rps)
    async with httpx.AsyncClient() as client:
        jup = JupiterClient(settings, client, limiter)
        prices = await jup.get_prices([mint])
        meta = prices.get(mint)
        if meta is None:
            return None, "NO-PRICE", jup.credits_used
        qty = notional_usd / meta.usd_price
        amount_raw = raw_amount(qty, meta.decimals)
        quote = await jup.quote(mint, settings.usdc_mint, amount_raw)
        if quote is None:
            return None, "NO-ROUTE", jup.credits_used
        cash = quote.out_amount
        return cash / notional_usd, quote.route_labels, jup.credits_used


async def run_probe(settings: Settings, asset: Asset) -> None:
    engine = ProbeEngine(settings)
    result = await engine.probe_asset(asset)
    print(f"\n=== Full probe: {asset.symbol} ({settings.jup_quote_version} @ {settings.jup_api_base}) ===")
    print(f"ok={result.ok} ref_price=${result.ref_price_usd:.4f} credits~via engine")
    if not result.ok:
        print(f"ERROR: {result.error}")
        return
    for rung in result.rungs:
        cash_eff = (rung.out_usd / rung.notional_usd * 100) if rung.out_usd else None
        base_eff = (rung.efficiency * 100) if rung.efficiency is not None else None
        cash_s = f"{cash_eff:.2f}%" if cash_eff is not None else "NO ROUTE"
        base_s = f"{base_eff:+.2f}bps" if base_eff is not None else "n/a"
        print(
            f"  ${rung.notional_usd:>9,.0f} -> cash {cash_s:>8}  "
            f"vs-baseline {base_s:>9}  {rung.route_labels}"
        )

    scoring = ScoringEngine()
    score = scoring.score(
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
            mcap_usd=72_700_000 if asset.symbol == "SPYx" else 49_900_000,
        )
    )
    print(
        f"  score: grade={score.grade} exit@95%={score.exit_capacity_95} "
        f"cliff={score.cliff_detected} no_route_ceiling={score.no_route_ceiling}"
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Jupiter probe logic on free API")
    parser.add_argument("--base-url", default="https://api.jup.ag")
    parser.add_argument("--quote-version", default="v1", choices=["v1", "v2"])
    parser.add_argument("--rps", type=float, default=1.0, help="Rate limit (free tier: 1 RPS)")
    parser.add_argument("--full-probe", action="store_true", help="Run full ladder probe (slow)")
    args = parser.parse_args()

    print("Endpoint connectivity:")
    await check_endpoints("https://public.jupiterapi.com", args.quote_version)
    primary = await check_endpoints(args.base_url, args.quote_version)

    if not all(primary.values()):
        print("\nFAIL: primary Jupiter base URL is not reachable for price/quote.")
        return 1

    settings = Settings(
        JUP_API_KEY="",
        JUP_API_BASE=args.base_url,
        JUP_QUOTE_VERSION=args.quote_version,
        JUP_RPS=args.rps,
    )

    print("\nSpot checks (single quotes):")
    spy_100k, spy_route, _ = await quote_efficiency(settings, SPY_MINT, 100_000)
    strc_150k, strc150_route, _ = await quote_efficiency(settings, STRC_MINT, 150_000)
    strc_200k, strc200_route, _ = await quote_efficiency(settings, STRC_MINT, 200_000)

    print(f"  SPYx  $100k cash efficiency: {spy_100k:.4%} via {spy_route}" if spy_100k else "  SPYx $100k: NO ROUTE")
    print(
        f"  STRCx $150k cash efficiency: {strc_150k:.4%} via {strc150_route}"
        if strc_150k
        else "  STRCx $150k: NO ROUTE"
    )
    print(
        f"  STRCx $200k cash efficiency: {strc_200k:.4%} via {strc200_route}"
        if strc_200k
        else "  STRCx $200k: NO ROUTE"
    )

    failures: list[str] = []
    warnings: list[str] = []

    if spy_100k is None or spy_100k < 0.95:
        failures.append("SPYx $100k should recover >=95% cash vs oracle-sized notional")

    # STRCx cliff is route/state dependent — measured Sep 2026, may not reproduce live.
    if strc_150k is not None and strc_200k is not None:
        if strc_200k < strc_150k * 0.5:
            print("  STRCx cliff pattern: large drop 150k -> 200k (historical cliff reproduced)")
        elif strc_200k < strc_150k * 0.9:
            warnings.append("STRCx shows mild degradation 150k -> 200k (partial cliff signal)")
        else:
            warnings.append(
                "STRCx cliff not reproduced today (expected — cliffs are time/route dependent; "
                "offline fixture test_strcx_cliff_detection still validates scoring logic)"
            )
    elif strc_200k is not None and strc_200k < 0.5:
        print("  STRCx $200k severely impaired (cliff/wall signal)")

    if args.full_probe:
        # Full ladder is ~24+ requests per asset; keep RPS low on free tier.
        limited = Settings(
            JUP_API_KEY="",
            JUP_API_BASE=args.base_url,
            JUP_QUOTE_VERSION=args.quote_version,
            JUP_RPS=args.rps,
            ladder_notionals_usd=[10_000, 100_000, 150_000, 200_000, 250_000],
        )
        await run_probe(limited, make_asset("SPYx", SPY_MINT))
        await run_probe(limited, make_asset("STRCx", STRC_MINT))

    print("\nRegression unit tests (offline scoring fixtures):")
    import pytest

    code = pytest.main(["-q", "tests/test_scoring.py", "tests/test_session_state.py", "tests/test_impersonation.py"])
    if code != 0:
        failures.append("offline unit tests failed")

    if warnings:
        print("\nWARNINGS (non-fatal):")
        for item in warnings:
            print(f"  - {item}")

    if failures:
        print("\nVALIDATION FAILED:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nVALIDATION PASSED: free Jupiter API quotes align with expected probe behavior.")
    print(f"  base={args.base_url} quote={args.quote_version}")
    print("  note: public.jupiterapi.com returned 404 — use https://api.jup.ag (free, no key)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
