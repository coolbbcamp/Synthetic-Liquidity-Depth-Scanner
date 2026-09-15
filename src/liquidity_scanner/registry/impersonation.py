from __future__ import annotations

import re
from dataclasses import dataclass

from liquidity_scanner.registry.sources import AssetRecord


@dataclass
class ImpersonationFlag:
    mint: str
    suspected_target_mint: str
    reason: str
    confidence: float


class ImpersonationDetector:
    BASE58_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")

    def __init__(self, verified_mints: set[str]) -> None:
        self.verified_mints = verified_mints

    def detect(self, assets: list[AssetRecord]) -> list[ImpersonationFlag]:
        flags: list[ImpersonationFlag] = []
        verified_by_symbol: dict[str, list[AssetRecord]] = {}
        for asset in assets:
            key = asset.symbol.upper()
            verified_by_symbol.setdefault(key, []).append(asset)

        for asset in assets:
            if asset.mint in self.verified_mints:
                continue

            # Symbol collision with a verified asset of same ticker.
            verified = [
                a for a in verified_by_symbol.get(asset.symbol.upper(), []) if a.mint in self.verified_mints
            ]
            if verified and asset.mint not in {v.mint for v in verified}:
                flags.append(
                    ImpersonationFlag(
                        mint=asset.mint,
                        suspected_target_mint=verified[0].mint,
                        reason="symbol_collision",
                        confidence=0.85,
                    )
                )

            # Name-field mint stuffing: mint address embedded in token name.
            embedded = self.BASE58_RE.findall(asset.name or "")
            for candidate in embedded:
                if candidate in self.verified_mints and candidate != asset.mint:
                    flags.append(
                        ImpersonationFlag(
                            mint=asset.mint,
                            suspected_target_mint=candidate,
                            reason="name_field_mint_stuffing",
                            confidence=0.95,
                        )
                    )

            # Pump suffix without registry verification.
            if asset.mint.endswith("pump") and asset.kind == "launch" and asset.verified_source != "stonkfun":
                flags.append(
                    ImpersonationFlag(
                        mint=asset.mint,
                        suspected_target_mint=verified[0].mint if verified else asset.quote_mint or "",
                        reason="unverified_pump_suffix",
                        confidence=0.6,
                    )
                )

        return flags
