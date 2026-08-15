"""Add private contact cards and contact exchange requests.

Revision ID: 20260815_0011
Revises: 20260813_0010
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260815_0011"
down_revision: Union[str, None] = "20260813_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contact_cards",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_contact_cards_version"),
    )
    op.create_table(
        "contact_methods",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("contact_cards.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("method_type", sa.String(16), primary_key=True),
        sa.Column("value", sa.String(254), nullable=False),
        sa.CheckConstraint(
            "method_type IN ('WECHAT','QQ','EMAIL')", name="ck_contact_methods_type"
        ),
    )
    op.create_table(
        "contact_exchange_requests",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.String(40), nullable=False),
        sa.Column(
            "requester_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "recipient_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("pending_key", sa.String(192), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id", "role_id"],
            ["project_roles.project_id", "project_roles.id"],
            ondelete="RESTRICT",
            name="fk_contact_exchange_requests_project_role",
        ),
        sa.UniqueConstraint("pending_key", name="uq_contact_exchange_requests_pending_key"),
        sa.CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REJECTED','CANCELLED')",
            name="ck_contact_exchange_requests_status",
        ),
        sa.CheckConstraint(
            "requester_id <> recipient_id", name="ck_contact_exchange_requests_not_self"
        ),
        sa.CheckConstraint(
            "(status = 'PENDING' AND pending_key IS NOT NULL) OR "
            "(status <> 'PENDING' AND pending_key IS NULL)",
            name="ck_contact_exchange_requests_pending_key",
        ),
    )
    op.create_index(
        "ix_contact_exchange_requests_requester_created",
        "contact_exchange_requests",
        ["requester_id", "created_at", "id"],
    )
    op.create_index(
        "ix_contact_exchange_requests_recipient_created",
        "contact_exchange_requests",
        ["recipient_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_table("contact_exchange_requests")
    op.drop_table("contact_methods")
    op.drop_table("contact_cards")
