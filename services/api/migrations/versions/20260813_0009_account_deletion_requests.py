"""Add auditable account deletion requests.

Revision ID: 20260813_0009
Revises: 20260813_0008
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0009"
down_revision: Union[str, None] = "20260813_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column(
            "pending_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
            unique=True,
        ),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING','CANCELLED','COMPLETED')",
            name="ck_account_deletion_requests_status",
        ),
        sa.CheckConstraint(
            "(status = 'PENDING' AND pending_user_id = user_id) OR "
            "(status <> 'PENDING' AND pending_user_id IS NULL)",
            name="ck_account_deletion_requests_pending_user",
        ),
    )
    op.create_index(
        "ix_account_deletion_requests_user_requested",
        "account_deletion_requests",
        ["user_id", "requested_at"],
    )


def downgrade() -> None:
    op.drop_table("account_deletion_requests")
