from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

from liquidity_scanner.config import Settings
from liquidity_scanner.db.models import Asset
from liquidity_scanner.logging import get_logger
from liquidity_scanner.probe.jupiter import JupiterClient, TokenPriceMeta, raw_amount
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter
from liquidity_scanner.scheduler.session_state import get_session_state

logger = get_logger(__name__)


@dataclass
class ProbeRungResult:
    direction: str
    notional_usd: float
    token_qty: float
    out_usd: float | None
    efficiency: float | None
    route_labels: str
    rfq_share: float | None
    no_route: bool
    leg1_route: str | None = None
    leg2_route: str | None = None
    binding_leg: str | None = None


@dataclass
class ProbeResult:
    mint: str
    probed_at: datetime
    session_state: str
    ref_price_usd: float
    baseline_exec_px: float | None
    ok: bool
    error: str | None = None
    rungs: list[ProbeRungResult] = field(default_factory=list)


class ProbeEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _rfq_share(self, route_labels: str) -> float:
        if not route_labels or route_labels == "NO-ROUTE":
            return 0.0
        labels = route_labels.split("+")
        rfq = sum(1 for label in labels if any(v in label for v in self.settings.rfq_venues))
        return rfq / len(labels)

    async def _median_quote_usd(
        self,
        jup: JupiterClient,
        input_mint: str,
        output_mint: str,
        amount_raw: int,
        output_decimals: int,
        samples: int | None = None,
    ) -> tuple[float | None, str]:
        if samples is None:
            samples = self.settings.quote_samples
        values: list[float] = []
        route = "NO-ROUTE"
        for _ in range(samples):
            quote = await jup.quote(input_mint, output_mint, amount_raw)
            if quote is None:
                continue
            values.append(quote.out_amount_raw / (10 ** output_decimals))
            route = quote.route_labels
        if not values:
            return None, "NO-ROUTE"
        return statistics.median(values), route

    async def probe_asset(self, asset: Asset, jup: JupiterClient | None = None) -> ProbeResult:
        now = datetime.now(UTC)
        session_state = get_session_state(now)
        if jup is not None:
            return await self._probe_asset_with_client(asset, jup, now, session_state)

        limiter = TokenBucketRateLimiter(self.settings.jup_rps)
        async with httpx.AsyncClient() as http_client:
            client = JupiterClient(self.settings, http_client, limiter)
            return await self._probe_asset_with_client(asset, client, now, session_state)

    async def _probe_asset_with_client(
        self,
        asset: Asset,
        jup: JupiterClient,
        now: datetime,
        session_state: str,
    ) -> ProbeResult:
        price_mints = [asset.mint]
        quote_mint = asset.quote_mint or self.settings.usdc_mint
        needs_quote_price = asset.kind == "launch" and quote_mint != self.settings.usdc_mint
        if needs_quote_price and quote_mint not in price_mints:
            price_mints.append(quote_mint)

        prices = await jup.get_prices(price_mints)
        meta = prices.get(asset.mint)
        if meta is None or meta.usd_price <= 0:
            return ProbeResult(
                mint=asset.mint,
                probed_at=now,
                session_state=session_state,
                ref_price_usd=0.0,
                baseline_exec_px=None,
                ok=False,
                error="no_price",
            )

        decimals = meta.decimals
        ref_price = meta.usd_price
        quote_meta: TokenPriceMeta = prices.get(quote_mint, meta)
        quote_decimals = quote_meta.decimals

        base_qty = self.settings.baseline_notional_usd / ref_price
        base_raw = raw_amount(base_qty, decimals)
        base_out, _ = await self._median_quote_usd(
            jup,
            asset.mint,
            self.settings.usdc_mint,
            base_raw,
            6,
            samples=1,
        )
        baseline_exec_px = (base_out / base_qty) if base_out else None

        rungs: list[ProbeRungResult] = []
        prev_eff: float | None = None
        prev_route: str | None = None

        for notional in self.settings.ladder_notionals_usd:
            qty = notional / ref_price
            amount_raw = raw_amount(qty, decimals)

            direct_out, direct_route = await self._median_quote_usd(
                jup, asset.mint, self.settings.usdc_mint, amount_raw, 6
            )
            cash_usd = direct_out
            cash_eff = (cash_usd / notional) if cash_usd else None

            leg1_route = "NO-ROUTE"
            leg2_route = "NO-ROUTE"
            leg1_usd = None
            binding_leg = None

            if asset.kind == "launch" and asset.quote_mint:
                leg1_raw_out, leg1_route = await self._median_quote_usd(
                    jup, asset.mint, asset.quote_mint, amount_raw, quote_decimals
                )
                if leg1_raw_out is not None:
                    leg1_usd = leg1_raw_out * quote_meta.usd_price
                    leg2_raw = raw_amount(leg1_raw_out, quote_decimals)
                    leg2_out, leg2_route = await self._median_quote_usd(
                        jup, asset.quote_mint, self.settings.usdc_mint, leg2_raw, 6
                    )
                    if leg2_out is not None and cash_usd is None:
                        cash_usd = leg2_out
                        cash_eff = cash_usd / notional

                if leg1_usd is not None and cash_usd is not None:
                    leg1_eff = leg1_usd / notional
                    if cash_eff is not None and leg1_eff - cash_eff > 0.005:
                        binding_leg = "leg2"
                    elif cash_eff is not None and leg1_eff < cash_eff - 0.005:
                        binding_leg = "leg1"
                    else:
                        binding_leg = "balanced"

            if cash_usd is None:
                rungs.append(
                    ProbeRungResult(
                        direction="sell",
                        notional_usd=notional,
                        token_qty=qty,
                        out_usd=None,
                        efficiency=None,
                        route_labels=direct_route,
                        rfq_share=self._rfq_share(direct_route),
                        no_route=True,
                        leg1_route=leg1_route,
                        leg2_route=leg2_route,
                        binding_leg="no_route",
                    )
                )
                prev_eff = None
                prev_route = direct_route
                continue

            if baseline_exec_px:
                efficiency = ((cash_usd / qty) - baseline_exec_px) / baseline_exec_px
            else:
                efficiency = (cash_usd / notional) - 1.0

            rung = ProbeRungResult(
                direction="sell",
                notional_usd=notional,
                token_qty=qty,
                out_usd=cash_usd,
                efficiency=efficiency,
                route_labels=direct_route,
                rfq_share=self._rfq_share(direct_route),
                no_route=False,
                leg1_route=leg1_route,
                leg2_route=leg2_route,
                binding_leg=binding_leg,
            )
            rungs.append(rung)

            if (
                self.settings.enable_cliff_bisection
                and prev_eff is not None
                and efficiency is not None
                and prev_route
                and direct_route != prev_route
                and (prev_eff - efficiency) > self.settings.cliff_efficiency_delta
            ):
                refined = await self._bisect_cliff(
                    jup,
                    asset.mint,
                    decimals,
                    ref_price,
                    baseline_exec_px,
                    rungs[-2].notional_usd,
                    notional,
                )
                if refined:
                    rungs.extend(refined)

            prev_eff = efficiency
            prev_route = direct_route

        return ProbeResult(
            mint=asset.mint,
            probed_at=now,
            session_state=session_state,
            ref_price_usd=ref_price,
            baseline_exec_px=baseline_exec_px,
            ok=True,
            rungs=rungs,
        )

    async def _bisect_cliff(
        self,
        jup: JupiterClient,
        mint: str,
        decimals: int,
        ref_price: float,
        baseline_exec_px: float | None,
        low_usd: float,
        high_usd: float,
        iterations: int = 4,
    ) -> list[ProbeRungResult]:
        results: list[ProbeRungResult] = []
        lo, hi = low_usd, high_usd
        for _ in range(iterations):
            mid = (lo + hi) / 2
            qty = mid / ref_price
            amount_raw = raw_amount(qty, decimals)
            out, route = await self._median_quote_usd(jup, mint, self.settings.usdc_mint, amount_raw, 6)
            if out is None:
                hi = mid
                continue
            if baseline_exec_px:
                eff = ((out / qty) - baseline_exec_px) / baseline_exec_px
            else:
                eff = (out / mid) - 1.0
            results.append(
                ProbeRungResult(
                    direction="sell",
                    notional_usd=mid,
                    token_qty=qty,
                    out_usd=out,
                    efficiency=eff,
                    route_labels=route,
                    rfq_share=self._rfq_share(route),
                    no_route=False,
                    binding_leg="cliff_refine",
                )
            )
            if eff < -0.5:
                hi = mid
            else:
                lo = mid
        return results
