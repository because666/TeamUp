"""Create identity, profile, and project foundation tables.

Revision ID: 20260811_0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260811_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("wechat_subject", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','DELETION_PENDING')", name="ck_users_status"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sessions_user_expires", "sessions", ["user_id", "expires_at"])
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nickname", sa.String(24), nullable=False),
        sa.Column("school", sa.String(40), nullable=False),
        sa.Column("major", sa.String(40), nullable=False),
        sa.Column("grade", sa.String(16), nullable=False),
        sa.Column("role_preference", sa.String(16), nullable=False),
        sa.Column("hours_per_week", sa.Integer(), nullable=False),
        sa.Column("bio", sa.String(240), nullable=False),
        sa.Column("visibility", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_profiles_hours_per_week"),
        sa.CheckConstraint("version > 0", name="ck_profiles_version"),
        sa.CheckConstraint("role_preference IN ('LEADER','MEMBER','FLEXIBLE')", name="ck_profiles_role_preference"),
    )
    op.create_table(
        "profile_skills",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("skill_name", sa.String(64), nullable=False),
    )
    op.create_table(
        "profile_collaboration_scenarios",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("scenario_name", sa.String(64), nullable=False),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(48), nullable=False),
        sa.Column("description", sa.String(600), nullable=False),
        sa.Column("direction", sa.String(32), nullable=False),
        sa.Column("competition", sa.String(80), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("team_info", sa.String(240), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','CLOSED')", name="ck_projects_status"),
        sa.CheckConstraint("version > 0", name="ck_projects_version"),
    )
    op.create_index("ix_projects_status_published", "projects", ["status", "published_at", "id"])
    op.create_table(
        "project_roles",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(48), nullable=False),
        sa.Column("headcount", sa.Integer(), nullable=False),
        sa.Column("hours_per_week", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.UniqueConstraint("project_id", "position", name="uq_project_roles_position"),
        sa.CheckConstraint("headcount > 0", name="ck_project_roles_headcount"),
        sa.CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_project_roles_hours_per_week"),
        sa.CheckConstraint("status IN ('OPEN','CLOSED')", name="ck_project_roles_status"),
    )
    op.create_table(
        "project_role_skills",
        sa.Column("role_id", sa.String(40), sa.ForeignKey("project_roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("skill_name", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("project_role_skills")
    op.drop_table("project_roles")
    op.drop_index("ix_projects_status_published", table_name="projects")
    op.drop_table("projects")
    op.drop_table("profile_collaboration_scenarios")
    op.drop_table("profile_skills")
    op.drop_table("profiles")
    op.drop_table("sessions")
    op.drop_table("users")
