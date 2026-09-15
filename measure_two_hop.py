#!/usr/bin/env python3
"""Measure stock-quoted launch exit paths: leg1 vs cash, and illusion gap."""

import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUP_QUOTE = "https://lite-api.jup.ag/swap/v1/quote"
JUP_PRICE = "https://lite-api.jup.ag/price/v3"
STONK_API = "https://www.stonkfun.xyz/api/public/v1"
SIZES_USD = [1_000, 10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
BASE_USD = 200
SLEEP = 0.9
HEADERS = {
    "User-Agent": "LiquidityDepthScanner/0.1 (research; contact: local)",
    "Accept": "application/json",
}


def get_json(url: str, retries: int = 6) -> Any:
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.2 * (i + 1))
    if last:
        raise last
    raise RuntimeError("request failed")


def jup_quote(input_mint: str, output_mint: str, amount: int) -> dict | None:
    qs = urllib.parse.urlencode(
        {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": "9000",
        }
    )
    try:
        return get_json(f"{JUP_QUOTE}?{qs}")
    except Exception:
        return None


def route_labels(quote: dict | None) -> str:
    if not quote:
        return "NO-ROUTE"
    parts = []
    for step in quote.get("routePlan", []):
        parts.append(step.get("swapInfo", {}).get("label", "?"))
    return "+".join(parts) if parts else "NO-ROUTE"


def token_meta(mint: str) -> tuple[float | None, int]:
    data = get_json(f"{JUP_PRICE}?ids={mint}")
    entry = data.get(mint)
    if not entry:
        return None, 6
    return float(entry["usdPrice"]), int(entry.get("decimals", 6))


@dataclass
class SizeResult:
    attempt_usd: float
    token_qty: float
    leg1_quote_out: float | None
    leg1_usd_value: float | None
    leg1_efficiency: float | None
    cash_usd: float | None
    cash_efficiency: float | None
    direct_usd: float | None
    direct_efficiency: float | None
    illusion_gap_pct: float | None
    quote_leg_loss_pct: float | None
    leg1_route: str
    leg2_route: str
    direct_route: str


@dataclass
class TokenStudy:
    symbol: str
    mint: str
    quote_symbol: str
    quote_mint: str
    pool: str | None
    ref_price_usd: float
    quote_price_usd: float
    market_cap_usd: float | None
    volume_24h_usd: float | None
    decimals: int
    sizes: list[SizeResult]


def fetch_stonkfun_token(mint: str) -> dict:
    return get_json(f"{STONK_API}/tokens/{mint}")["data"]["token"]


def raw_amount(qty: float, decimals: int) -> int:
    return int(math.floor(qty * (10 ** decimals)))


def study_token(mint: str, quote_mint: str | None = None, decimals: int | None = None) -> TokenStudy:
    meta = fetch_stonkfun_token(mint)
    time.sleep(SLEEP)
    quote = meta["quote"]
    quote_mint = quote_mint or quote["mint"]
    ref, token_decimals = token_meta(mint)
    time.sleep(SLEEP)
    qpx, quote_decimals = token_meta(quote_mint)
    time.sleep(SLEEP)
    if decimals is None:
        decimals = token_decimals
    if not ref or not qpx:
        raise RuntimeError(f"missing price for {mint}")

    market = meta.get("market", {})
    sizes: list[SizeResult] = []

    for usd in SIZES_USD:
        qty = usd / ref
        raw = raw_amount(qty, decimals)
        leg1 = jup_quote(mint, quote_mint, raw)
        time.sleep(SLEEP)
        leg2 = None
        leg1_quote_out = None
        leg1_usd = None
        cash_usd = None
        if leg1:
            leg1_quote_out = int(leg1["outAmount"]) / (10 ** quote_decimals)
            leg1_usd = leg1_quote_out * qpx
            leg2 = jup_quote(quote_mint, USDC, int(leg1["outAmount"]))
            time.sleep(SLEEP)
            if leg2:
                cash_usd = int(leg2["outAmount"]) / 1e6

        direct = jup_quote(mint, USDC, raw)
        time.sleep(SLEEP)
        direct_usd = int(direct["outAmount"]) / 1e6 if direct else None

        leg1_eff = leg1_usd / usd if leg1_usd is not None else None
        cash_eff = cash_usd / usd if cash_usd is not None else None
        direct_eff = direct_usd / usd if direct_usd is not None else None
        illusion = None
        quote_leg_loss = None
        if leg1_usd is not None and cash_usd is not None and leg1_usd > 0:
            illusion = ((leg1_usd - cash_usd) / usd) * 100
            quote_leg_loss = ((leg1_usd - cash_usd) / leg1_usd) * 100

        sizes.append(
            SizeResult(
                attempt_usd=usd,
                token_qty=qty,
                leg1_quote_out=leg1_quote_out,
                leg1_usd_value=leg1_usd,
                leg1_efficiency=leg1_eff,
                cash_usd=cash_usd,
                cash_efficiency=cash_eff,
                direct_usd=direct_usd,
                direct_efficiency=direct_eff,
                illusion_gap_pct=illusion,
                quote_leg_loss_pct=quote_leg_loss,
                leg1_route=route_labels(leg1),
                leg2_route=route_labels(leg2),
                direct_route=route_labels(direct),
            )
        )

    return TokenStudy(
        symbol=meta["symbol"],
        mint=mint,
        quote_symbol=quote["symbol"],
        quote_mint=quote_mint,
        pool=meta.get("pool"),
        ref_price_usd=ref,
        quote_price_usd=qpx,
        market_cap_usd=market.get("marketCapUsd"),
        volume_24h_usd=market.get("volume24hUsd"),
        decimals=decimals,
        sizes=sizes,
    )


def main() -> None:
    candidates = [
        ("6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx", None),  # STONK/SPYx flagship
        ("EXinYuNbxamDtbpkqR6RQJ9XWgUb5y2rCBMkAWxEazYt", None),  # SNP500/SPYx
        ("3w5cKpkfz2TAS22oXhMSZGjpsK6URL5d5db2thvwMtVx", None),  # FTR/TSLAx
        ("Aigf5pKPyZW8nzxCrHEisE4tZMiUhFpKie8mYE7cmj6c", None),  # NVDGE/NVDAx
    ]

    results = []
    for mint, quote in candidates:
        print(f"=== measuring {mint[:8]}... ===", flush=True)
        try:
            study = study_token(mint, quote)
            results.append(asdict(study))
            print(
                f"{study.symbol}/{study.quote_symbol}  mcap=${study.market_cap_usd:,.0f}  "
                f"ref=${study.ref_price_usd:.6f}",
                flush=True,
            )
            for s in study.sizes:
                if s.cash_efficiency is None:
                    line = f"  ${s.attempt_usd:>9,.0f}  leg1={s.leg1_efficiency}  cash=NO-ROUTE"
                else:
                    gap = f"{s.illusion_gap_pct:.2f}%" if s.illusion_gap_pct is not None else "n/a"
                    line = (
                        f"  ${s.attempt_usd:>9,.0f}  leg1={s.leg1_efficiency*100:6.2f}%  "
                        f"cash={s.cash_efficiency*100:6.2f}%  hidden={gap}"
                    )
                print(line, flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}", flush=True)
            results.append({"mint": mint, "error": str(exc)})

    out = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": {
            "leg1": "token -> quote stock, valued at quote USD oracle",
            "cash": "token -> quote stock -> USDC composed",
            "direct": "token -> USDC single Jupiter quote",
            "illusion_gap_pct": "(leg1_usd_value - cash_usd) / attempt_usd * 100",
            "note": "attempt_usd uses token oracle price * qty; measures exit of a position notionally worth X",
        },
        "results": results,
    }
    with open("two_hop_measurement.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("saved two_hop_measurement.json", flush=True)


if __name__ == "__main__":
    main()
