"""Add project members and capacity query indexes.

Revision ID: 20260812_0003
Revises: 20260812_0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0003"
down_revision: Union[str, None] = "20260812_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_roles") as batch_op:
        batch_op.create_unique_constraint("uq_project_roles_project_id_id", ["project_id", "id"])
    op.create_table(
        "project_members",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.String(40), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
        sa.ForeignKeyConstraint(
            ["project_id", "role_id"],
            ["project_roles.project_id", "project_roles.id"],
            ondelete="RESTRICT",
            name="fk_project_members_project_role",
        ),
        sa.CheckConstraint("status IN ('ACTIVE')", name="ck_project_members_status"),
    )
    op.create_index("ix_project_members_role_status", "project_members", ["role_id", "status"])
    op.create_index("ix_project_members_user_status", "project_members", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("project_members")
    with op.batch_alter_table("project_roles") as batch_op:
        batch_op.drop_constraint("uq_project_roles_project_id_id", type_="unique")
