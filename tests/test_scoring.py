import json
from pathlib import Path

from liquidity_scanner.scoring.engine import RungInput, ScoringEngine, ScoringInput


def load_fixture(name: str) -> dict:
    data = json.loads(Path("tests/fixtures/regression_rungs.json").read_text(encoding="utf-8"))
    return data[name]


def make_rungs(raw_rungs: list[dict]) -> list[RungInput]:
    out = []
    for r in raw_rungs:
        out.append(
            RungInput(
                notional_usd=r["notional_usd"],
                out_usd=r.get("out_usd"),
                efficiency=None,
                no_route=r.get("no_route", False),
                route_labels=r.get("route_labels"),
                rfq_share=0.5 if "Riptide" in (r.get("route_labels") or "") else 0.0,
                binding_leg=None,
            )
        )
    return out


def test_spyx_100k_exit_capacity():
    fixture = load_fixture("SPYx_100k")
    engine = ScoringEngine()
    result = engine.score(ScoringInput(rungs=make_rungs(fixture["rungs"]), mcap_usd=fixture["mcap_usd"]))
    rung = next(r for r in fixture["rungs"] if r["notional_usd"] == 100000)
    assert (rung["out_usd"] / 100000) >= fixture["expected_efficiency_at_100k_min"]
    assert result.exit_capacity_95 is not None
    assert result.exit_capacity_95 >= 50000


def test_stonk_100k_cash_efficiency():
    fixture = load_fixture("STONK_100k")
    rung = fixture["rungs"][0]
    assert (rung["out_usd"] / rung["notional_usd"]) >= fixture["expected_cash_efficiency_at_100k_min"]


def test_strcx_cliff_detection():
    fixture = load_fixture("STRCx_cliff")
    engine = ScoringEngine()
    result = engine.score(ScoringInput(rungs=make_rungs(fixture["rungs"]), mcap_usd=49_900_000))
    assert result.cliff_detected is True
    assert result.cliff_notional == 200000


def test_ftr_no_route_ceiling():
    fixture = load_fixture("FTR_no_route")
    engine = ScoringEngine()
    result = engine.score(ScoringInput(rungs=make_rungs(fixture["rungs"]), mcap_usd=56_836))
    assert result.no_route_ceiling == fixture["expected_no_route_ceiling"]


def test_methodology_guard_rejects_flat_offset_curve():
    """Flat efficiency across sizes with nonzero offset indicates external-price baseline bug."""
    rungs = [
        RungInput(1000, 900, -0.10, False, "A", 0.0, None),
        RungInput(10000, 9000, -0.10, False, "A", 0.0, None),
        RungInput(100000, 90000, -0.10, False, "A", 0.0, None),
    ]
    efficiencies = [r.out_usd / r.notional_usd for r in rungs if r.out_usd]
    assert max(efficiencies) - min(efficiencies) < 0.001
    assert efficiencies[0] < 0.95
