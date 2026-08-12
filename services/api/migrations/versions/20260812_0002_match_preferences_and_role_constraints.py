"""Add match preferences and structured project role constraints.

Revision ID: 20260812_0002
Revises: 20260811_0001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0002"
down_revision: Union[str, None] = "20260811_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_roles") as batch_op:
        batch_op.add_column(
            sa.Column("collaboration_role", sa.String(16), nullable=False, server_default="MEMBER")
        )
        batch_op.create_check_constraint(
            "ck_project_roles_collaboration_role",
            "collaboration_role IN ('LEADER','MEMBER','FLEXIBLE')",
        )
    with op.batch_alter_table("project_role_skills") as batch_op:
        batch_op.add_column(sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index(
            "ix_project_role_skills_skill_required",
            ["skill_name", "required", "role_id"],
        )

    op.create_table(
        "match_preferences",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_match_preferences_version"),
    )
    op.create_table(
        "match_preference_directions",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("match_preferences.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("direction_code", sa.String(64), nullable=False),
        sa.UniqueConstraint("user_id", "direction_code", name="uq_match_preference_direction"),
    )
    op.create_index(
        "ix_match_preference_direction_code",
        "match_preference_directions",
        ["direction_code", "user_id"],
    )
    op.create_table(
        "match_preference_availability_slots",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("match_preferences.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.CheckConstraint("timezone = 'Asia/Shanghai'", name="ck_match_preference_slots_timezone"),
        sa.CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_match_preference_slots_weekday"),
        sa.CheckConstraint("start_minute BETWEEN 0 AND 1439", name="ck_match_preference_slots_start"),
        sa.CheckConstraint("end_minute BETWEEN 1 AND 1440", name="ck_match_preference_slots_end"),
        sa.CheckConstraint("start_minute < end_minute", name="ck_match_preference_slots_range"),
    )
    op.create_table(
        "project_collaboration_scenarios",
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("scenario_code", sa.String(64), nullable=False),
        sa.UniqueConstraint("project_id", "scenario_code", name="uq_project_collaboration_scenario"),
    )
    op.create_table(
        "project_role_availability_slots",
        sa.Column(
            "role_id",
            sa.String(40),
            sa.ForeignKey("project_roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.CheckConstraint("timezone = 'Asia/Shanghai'", name="ck_project_role_slots_timezone"),
        sa.CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_project_role_slots_weekday"),
        sa.CheckConstraint("start_minute BETWEEN 0 AND 1439", name="ck_project_role_slots_start"),
        sa.CheckConstraint("end_minute BETWEEN 1 AND 1440", name="ck_project_role_slots_end"),
        sa.CheckConstraint("start_minute < end_minute", name="ck_project_role_slots_range"),
    )


def downgrade() -> None:
    op.drop_table("project_role_availability_slots")
    op.drop_table("project_collaboration_scenarios")
    op.drop_table("match_preference_availability_slots")
    op.drop_index("ix_match_preference_direction_code", table_name="match_preference_directions")
    op.drop_table("match_preference_directions")
    op.drop_table("match_preferences")
    with op.batch_alter_table("project_role_skills") as batch_op:
        batch_op.drop_index("ix_project_role_skills_skill_required")
        batch_op.drop_column("required")
    with op.batch_alter_table("project_roles") as batch_op:
        batch_op.drop_constraint("ck_project_roles_collaboration_role", type_="check")
        batch_op.drop_column("collaboration_role")
