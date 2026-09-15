from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"

    mint: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(16))
    issuer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    listing_provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quote_mint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quote_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pool: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    redemption_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    tier: Mapped[str] = mapped_column(String(8), default="C")

    probes: Mapped[list[Probe]] = relationship(back_populates="asset")
    scores: Mapped[list[Score]] = relationship(back_populates="asset")


class Probe(Base):
    __tablename__ = "probes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String(64), ForeignKey("assets.mint"), index=True)
    probed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    session_state: Mapped[str] = mapped_column(String(16))
    ref_price_usd: Mapped[float] = mapped_column(Float)
    baseline_exec_px: Mapped[float | None] = mapped_column(Float, nullable=True)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(String(128), nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="probes")
    rungs: Mapped[list[ProbeRung]] = relationship(back_populates="probe", cascade="all, delete-orphan")


class ProbeRung(Base):
    __tablename__ = "probe_rungs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    probe_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("probes.id"), index=True)
    direction: Mapped[str] = mapped_column(String(8), default="sell")
    notional_usd: Mapped[float] = mapped_column(Float)
    token_qty: Mapped[float] = mapped_column(Float)
    out_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_labels: Mapped[str | None] = mapped_column(Text, nullable=True)
    rfq_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    no_route: Mapped[bool] = mapped_column(Boolean, default=False)
    leg1_route: Mapped[str | None] = mapped_column(Text, nullable=True)
    leg2_route: Mapped[str | None] = mapped_column(Text, nullable=True)
    binding_leg: Mapped[str | None] = mapped_column(String(16), nullable=True)

    probe: Mapped[Probe] = relationship(back_populates="rungs")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String(64), ForeignKey("assets.mint"), index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    exit_capacity_99: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_capacity_95: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_capacity_90: Mapped[float | None] = mapped_column(Float, nullable=True)
    no_route_ceiling: Mapped[float | None] = mapped_column(Float, nullable=True)
    mcap_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    mcap_exit_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    binding_leg: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cliff_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    cliff_notional: Mapped[float | None] = mapped_column(Float, nullable=True)
    rfq_dependence: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(8), nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="scores")


class ImpersonationFlag(Base):
    __tablename__ = "impersonation_flags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String(64), index=True)
    suspected_target_mint: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    prev_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="warning")
