from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, foreign, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    wechat_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (CheckConstraint("status IN ('ACTIVE','SUSPENDED','DELETION_PENDING')", name="ck_users_status"),)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (Index("ix_sessions_user_expires", "user_id", "expires_at"),)


class BlockRow(Base):
    __tablename__ = "blocks"

    blocker_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blocked_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_blocks_blocked_blocker", "blocked_id", "blocker_id"),
        CheckConstraint("blocker_id <> blocked_id", name="ck_blocks_not_self"),
    )


class ProfileRow(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(24), nullable=False)
    school: Mapped[str] = mapped_column(String(40), nullable=False)
    major: Mapped[str] = mapped_column(String(40), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    role_preference: Mapped[str] = mapped_column(String(16), nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    bio: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    visibility: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    skills: Mapped[list[ProfileSkillRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    scenarios: Mapped[list[ProfileScenarioRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_profiles_hours_per_week"),
        CheckConstraint("version > 0", name="ck_profiles_version"),
        CheckConstraint("role_preference IN ('LEADER','MEMBER','FLEXIBLE')", name="ck_profiles_role_preference"),
    )


class ProfileSkillRow(Base):
    __tablename__ = "profile_skills"

    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)


class ProfileScenarioRow(Base):
    __tablename__ = "profile_collaboration_scenarios"

    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)


class MatchPreferenceRow(Base):
    __tablename__ = "match_preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    directions: Mapped[list[MatchPreferenceDirectionRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    availability_slots: Mapped[list[MatchPreferenceAvailabilitySlotRow]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (CheckConstraint("version > 0", name="ck_match_preferences_version"),)


class MatchPreferenceDirectionRow(Base):
    __tablename__ = "match_preference_directions"

    user_id: Mapped[str] = mapped_column(ForeignKey("match_preferences.user_id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    direction_code: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "direction_code", name="uq_match_preference_direction"),
        Index("ix_match_preference_direction_code", "direction_code", "user_id"),
    )


class MatchPreferenceAvailabilitySlotRow(Base):
    __tablename__ = "match_preference_availability_slots"

    user_id: Mapped[str] = mapped_column(ForeignKey("match_preferences.user_id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Shanghai")
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("timezone = 'Asia/Shanghai'", name="ck_match_preference_slots_timezone"),
        CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_match_preference_slots_weekday"),
        CheckConstraint("start_minute BETWEEN 0 AND 1439", name="ck_match_preference_slots_start"),
        CheckConstraint("end_minute BETWEEN 1 AND 1440", name="ck_match_preference_slots_end"),
        CheckConstraint("start_minute < end_minute", name="ck_match_preference_slots_range"),
    )


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(48), nullable=False)
    description: Mapped[str] = mapped_column(String(600), nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    competition: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    team_info: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    roles: Mapped[list[ProjectRoleRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    scenarios: Mapped[list[ProjectScenarioRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    members: Mapped[list[ProjectMemberRow]] = relationship(
        primaryjoin=lambda: ProjectRow.id == foreign(ProjectMemberRow.project_id),
        viewonly=True,
        lazy="selectin",
    )
    __table_args__ = (
        Index("ix_projects_status_published", "status", "published_at", "id"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','CLOSED')", name="ck_projects_status"),
        CheckConstraint("version > 0", name="ck_projects_version"),
    )


class ProjectRoleRow(Base):
    __tablename__ = "project_roles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(48), nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")
    collaboration_role: Mapped[str] = mapped_column(String(16), nullable=False, default="MEMBER")

    skills: Mapped[list[ProjectRoleSkillRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    availability_slots: Mapped[list[ProjectRoleAvailabilitySlotRow]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    __table_args__ = (
        UniqueConstraint("project_id", "position", name="uq_project_roles_position"),
        UniqueConstraint("project_id", "id", name="uq_project_roles_project_id_id"),
        CheckConstraint("headcount > 0", name="ck_project_roles_headcount"),
        CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_project_roles_hours_per_week"),
        CheckConstraint("status IN ('OPEN','CLOSED')", name="ck_project_roles_status"),
        CheckConstraint(
            "collaboration_role IN ('LEADER','MEMBER','FLEXIBLE')",
            name="ck_project_roles_collaboration_role",
        ),
    )


class ProjectRoleSkillRow(Base):
    __tablename__ = "project_role_skills"

    role_id: Mapped[str] = mapped_column(String(40), ForeignKey("project_roles.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (Index("ix_project_role_skills_skill_required", "skill_name", "required", "role_id"),)


class ProjectRoleAvailabilitySlotRow(Base):
    __tablename__ = "project_role_availability_slots"

    role_id: Mapped[str] = mapped_column(String(40), ForeignKey("project_roles.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Shanghai")
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("timezone = 'Asia/Shanghai'", name="ck_project_role_slots_timezone"),
        CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_project_role_slots_weekday"),
        CheckConstraint("start_minute BETWEEN 0 AND 1439", name="ck_project_role_slots_start"),
        CheckConstraint("end_minute BETWEEN 1 AND 1440", name="ck_project_role_slots_end"),
        CheckConstraint("start_minute < end_minute", name="ck_project_role_slots_range"),
    )


class ProjectScenarioRow(Base):
    __tablename__ = "project_collaboration_scenarios"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_code: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("project_id", "scenario_code", name="uq_project_collaboration_scenario"),)


class ProjectMemberRow(Base):
    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_id: Mapped[str] = mapped_column(String(40), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "role_id"],
            ["project_roles.project_id", "project_roles.id"],
            ondelete="RESTRICT",
            name="fk_project_members_project_role",
        ),
        UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
        Index("ix_project_members_role_status", "role_id", "status"),
        Index("ix_project_members_user_status", "user_id", "status"),
        CheckConstraint("status IN ('ACTIVE')", name="ck_project_members_status"),
    )
