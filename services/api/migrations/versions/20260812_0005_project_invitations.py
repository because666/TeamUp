"""Add project role invitations.

Revision ID: 20260812_0005
Revises: 20260812_0004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0005"
down_revision: Union[str, None] = "20260812_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.String(40), nullable=False),
        sa.Column("inviter_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("invitee_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("pending_key", sa.String(128), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id", "role_id"],
            ["project_roles.project_id", "project_roles.id"],
            ondelete="RESTRICT",
            name="fk_invitations_project_role",
        ),
        sa.UniqueConstraint("pending_key", name="uq_invitations_pending_key"),
        sa.CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REJECTED','EXPIRED','CANCELLED')",
            name="ck_invitations_status",
        ),
        sa.CheckConstraint("inviter_id <> invitee_id", name="ck_invitations_not_self"),
        sa.CheckConstraint(
            "(status = 'PENDING' AND pending_key IS NOT NULL) OR "
            "(status <> 'PENDING' AND pending_key IS NULL)",
            name="ck_invitations_pending_key",
        ),
    )
    op.create_index(
        "ix_invitations_invitee_status_expires",
        "invitations",
        ["invitee_id", "status", "expires_at"],
    )
    op.create_index("ix_invitations_project_status", "invitations", ["project_id", "status"])


def downgrade() -> None:
    op.drop_table("invitations")
