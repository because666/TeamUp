"""Add directional user block relationships.

Revision ID: 20260812_0004
Revises: 20260812_0003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0004"
down_revision: Union[str, None] = "20260812_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blocks",
        sa.Column("blocker_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("blocked_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("blocker_id <> blocked_id", name="ck_blocks_not_self"),
    )
    op.create_index("ix_blocks_blocked_blocker", "blocks", ["blocked_id", "blocker_id"])


def downgrade() -> None:
    op.drop_table("blocks")
