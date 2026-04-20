"""Step 07 audit and alert model refinements."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260420_01"
down_revision = "20260416_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for value in ("context_assembled", "tool_called", "agent_output_recorded"):
        op.execute(f"ALTER TYPE audit_event_type_enum ADD VALUE IF NOT EXISTS '{value}'")

    op.add_column(
        "alerts",
        sa.Column("related_audit_event_id", sa.String(length=128), nullable=True),
    )
    op.create_foreign_key(
        "fk_alerts_related_audit_event_id_audit_records",
        "alerts",
        "audit_records",
        ["related_audit_event_id"],
        ["audit_event_id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_alerts_related_audit_event_id",
        "alerts",
        ["related_audit_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_alerts_related_audit_event_id", table_name="alerts")
    op.drop_constraint("fk_alerts_related_audit_event_id_audit_records", "alerts", type_="foreignkey")
    op.drop_column("alerts", "related_audit_event_id")

    # PostgreSQL enum values are intentionally left in place on downgrade to avoid
    # recreating the enum while older rows may still reference the added values.
