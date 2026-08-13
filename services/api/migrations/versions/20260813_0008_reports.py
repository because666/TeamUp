"""Add user-submitted safety reports.

Revision ID: 20260813_0008
Revises: 20260813_0007
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0008"
down_revision: Union[str, None] = "20260813_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("reporter_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("pending_key", sa.String(192), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("target_type IN ('USER','PROJECT','MESSAGE')", name="ck_reports_target_type"),
        sa.CheckConstraint(
            "reason IN ('SPAM','HARASSMENT','FRAUD','INAPPROPRIATE_CONTENT','OTHER')",
            name="ck_reports_reason",
        ),
        sa.CheckConstraint("status IN ('PENDING','REVIEWED','DISMISSED','ACTIONED')", name="ck_reports_status"),
        sa.CheckConstraint(
            "(status = 'PENDING' AND pending_key IS NOT NULL) OR "
            "(status <> 'PENDING' AND pending_key IS NULL)",
            name="ck_reports_pending_key",
        ),
    )
    op.create_index("ix_reports_status_created", "reports", ["status", "created_at"])
    op.create_index("ix_reports_target", "reports", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_table("reports")
