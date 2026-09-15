from liquidity_scanner.constants import XSTOCK_MINTS
from liquidity_scanner.registry.impersonation import ImpersonationDetector
from liquidity_scanner.registry.sources import AssetRecord


def test_name_field_mint_stuffing_detected():
    genuine = XSTOCK_MINTS["HOODx"]
    fake = AssetRecord(
        mint="FakeMint1234567890123456789012345678901234",
        symbol="HOODx",
        name=f"Robinhood xStock {genuine}",
        kind="launch",
        quote_mint=genuine,
        quote_symbol="HOODx",
    )
    detector = ImpersonationDetector(set(XSTOCK_MINTS.values()))
    flags = detector.detect([fake])
    assert any(f.reason == "name_field_mint_stuffing" for f in flags)
