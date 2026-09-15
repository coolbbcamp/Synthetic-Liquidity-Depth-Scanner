from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class RungInput:
    notional_usd: float
    out_usd: float | None
    efficiency: float | None
    no_route: bool
    route_labels: str | None
    rfq_share: float | None
    binding_leg: str | None


@dataclass
class ScoringInput:
    rungs: list[RungInput]
    mcap_usd: float | None
    cliff_efficiency_delta: float = 0.15


@dataclass
class ScoringOutput:
    exit_capacity_99: float | None
    exit_capacity_95: float | None
    exit_capacity_90: float | None
    no_route_ceiling: float | None
    mcap_exit_ratio: float | None
    binding_leg: str | None
    cliff_detected: bool
    cliff_notional: float | None
    rfq_dependence: float | None
    grade: str


class ScoringEngine:
    THRESHOLDS = (0.99, 0.95, 0.90)

    def score(self, data: ScoringInput) -> ScoringOutput:
        valid = [r for r in data.rungs if not r.no_route and r.out_usd is not None]
        no_route = [r for r in data.rungs if r.no_route]
        no_route_ceiling = min((r.notional_usd for r in no_route), default=None)

        capacities = {
            0.99: self._capacity_at_efficiency(valid, 0.99),
            0.95: self._capacity_at_efficiency(valid, 0.95),
            0.90: self._capacity_at_efficiency(valid, 0.90),
        }

        cliff_detected, cliff_notional = self._detect_cliff(valid, data.cliff_efficiency_delta)
        rfq = self._avg_rfq(valid)
        binding = self._dominant_binding(data.rungs)
        mcap_ratio = None
        if data.mcap_usd and capacities[0.95]:
            mcap_ratio = data.mcap_usd / capacities[0.95]

        grade = self._grade(capacities[0.95], no_route_ceiling, cliff_detected, mcap_ratio)
        return ScoringOutput(
            exit_capacity_99=capacities[0.99],
            exit_capacity_95=capacities[0.95],
            exit_capacity_90=capacities[0.90],
            no_route_ceiling=no_route_ceiling,
            mcap_exit_ratio=mcap_ratio,
            binding_leg=binding,
            cliff_detected=cliff_detected,
            cliff_notional=cliff_notional,
            rfq_dependence=rfq,
            grade=grade,
        )

    def _cash_efficiency(self, rung: RungInput) -> float | None:
        if rung.out_usd is None:
            return None
        return rung.out_usd / rung.notional_usd

    def _capacity_at_efficiency(self, rungs: list[RungInput], threshold: float) -> float | None:
        if not rungs:
            return None
        sorted_rungs = sorted(rungs, key=lambda r: r.notional_usd)
        last_good = None
        for rung in sorted_rungs:
            eff = self._cash_efficiency(rung)
            if eff is None:
                break
            if eff >= threshold:
                last_good = rung.notional_usd
            else:
                if last_good is not None:
                    return self._interpolate(last_good, rung.notional_usd, threshold, rungs)
                return 0.0
        return last_good

    def _interpolate(
        self,
        low_notional: float,
        high_notional: float,
        threshold: float,
        rungs: list[RungInput],
    ) -> float:
        low = next(r for r in rungs if r.notional_usd == low_notional)
        high = next(r for r in rungs if r.notional_usd == high_notional)
        low_eff = self._cash_efficiency(low) or threshold
        high_eff = self._cash_efficiency(high) or 0.0
        if math.isclose(low_eff, high_eff):
            return low_notional
        ratio = (threshold - high_eff) / (low_eff - high_eff)
        ratio = max(0.0, min(1.0, ratio))
        return math.exp(math.log(low_notional) + ratio * (math.log(high_notional) - math.log(low_notional)))

    def _detect_cliff(self, rungs: list[RungInput], delta: float) -> tuple[bool, float | None]:
        sorted_rungs = sorted(rungs, key=lambda r: r.notional_usd)
        for prev, curr in zip(sorted_rungs, sorted_rungs[1:]):
            prev_eff = self._cash_efficiency(prev)
            curr_eff = self._cash_efficiency(curr)
            if prev_eff is None or curr_eff is None:
                continue
            if (prev_eff - curr_eff) > delta and prev.route_labels != curr.route_labels:
                return True, curr.notional_usd
        return False, None

    def _avg_rfq(self, rungs: list[RungInput]) -> float | None:
        shares = [r.rfq_share for r in rungs if r.rfq_share is not None]
        if not shares:
            return None
        return sum(shares) / len(shares)

    def _dominant_binding(self, rungs: list[RungInput]) -> str | None:
        counts: dict[str, int] = {}
        for rung in rungs:
            if rung.binding_leg:
                counts[rung.binding_leg] = counts.get(rung.binding_leg, 0) + 1
        if not counts:
            return None
        return max(counts, key=counts.get)

    def _grade(
        self,
        cap_95: float | None,
        no_route_ceiling: float | None,
        cliff: bool,
        mcap_ratio: float | None,
    ) -> str:
        if cliff:
            return "D"
        if no_route_ceiling is not None and no_route_ceiling <= 10_000:
            return "D"
        if cap_95 is not None and cap_95 >= 250_000:
            return "A"
        if cap_95 is not None and cap_95 >= 50_000:
            return "B"
        if cap_95 is not None and cap_95 >= 10_000:
            return "C"
        if mcap_ratio is not None and mcap_ratio > 1000:
            return "F"
        return "D"
