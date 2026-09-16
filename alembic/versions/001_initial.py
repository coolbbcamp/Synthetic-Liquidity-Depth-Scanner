"""initial schema

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("mint", sa.String(length=64), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("issuer", sa.String(length=128), nullable=True),
        sa.Column("listing_provider", sa.String(length=128), nullable=True),
        sa.Column("quote_mint", sa.String(length=64), nullable=True),
        sa.Column("quote_symbol", sa.String(length=32), nullable=True),
        sa.Column("pool", sa.String(length=64), nullable=True),
        sa.Column("decimals", sa.Integer(), nullable=True),
        sa.Column("verified_source", sa.String(length=64), nullable=True),
        sa.Column("redemption_terms", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tier", sa.String(length=8), nullable=False, server_default="C"),
    )
    op.create_table(
        "impersonation_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mint", sa.String(length=64), nullable=False),
        sa.Column("suspected_target_mint", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_impersonation_flags_mint", "impersonation_flags", ["mint"])
    op.create_table(
        "probes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mint", sa.String(length=64), sa.ForeignKey("assets.mint"), nullable=False),
        sa.Column("probed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_state", sa.String(length=16), nullable=False),
        sa.Column("ref_price_usd", sa.Float(), nullable=False),
        sa.Column("baseline_exec_px", sa.Float(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("error", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_probes_mint", "probes", ["mint"])
    op.create_index("ix_probes_probed_at", "probes", ["probed_at"])
    op.create_table(
        "probe_rungs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("probe_id", sa.Integer(), sa.ForeignKey("probes.id"), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False, server_default="sell"),
        sa.Column("notional_usd", sa.Float(), nullable=False),
        sa.Column("token_qty", sa.Float(), nullable=False),
        sa.Column("out_usd", sa.Float(), nullable=True),
        sa.Column("efficiency", sa.Float(), nullable=True),
        sa.Column("route_labels", sa.Text(), nullable=True),
        sa.Column("rfq_share", sa.Float(), nullable=True),
        sa.Column("no_route", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("leg1_route", sa.Text(), nullable=True),
        sa.Column("leg2_route", sa.Text(), nullable=True),
        sa.Column("binding_leg", sa.String(length=16), nullable=True),
    )
    op.create_index("ix_probe_rungs_probe_id", "probe_rungs", ["probe_id"])
    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mint", sa.String(length=64), sa.ForeignKey("assets.mint"), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_capacity_99", sa.Float(), nullable=True),
        sa.Column("exit_capacity_95", sa.Float(), nullable=True),
        sa.Column("exit_capacity_90", sa.Float(), nullable=True),
        sa.Column("no_route_ceiling", sa.Float(), nullable=True),
        sa.Column("mcap_usd", sa.Float(), nullable=True),
        sa.Column("mcap_exit_ratio", sa.Float(), nullable=True),
        sa.Column("binding_leg", sa.String(length=16), nullable=True),
        sa.Column("cliff_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cliff_notional", sa.Float(), nullable=True),
        sa.Column("rfq_dependence", sa.Float(), nullable=True),
        sa.Column("grade", sa.String(length=8), nullable=True),
    )
    op.create_index("ix_scores_mint", "scores", ["mint"])
    op.create_index("ix_scores_computed_at", "scores", ["computed_at"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mint", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prev_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="warning"),
    )
    op.create_index("ix_alerts_mint", "alerts", ["mint"])
    op.create_index("ix_alerts_detected_at", "alerts", ["detected_at"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("scores")
    op.drop_table("probe_rungs")
    op.drop_table("probes")
    op.drop_table("impersonation_flags")
    op.drop_table("assets")
