from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

    skills: Mapped[list[ProjectRoleSkillRow]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    __table_args__ = (
        UniqueConstraint("project_id", "position", name="uq_project_roles_position"),
        CheckConstraint("headcount > 0", name="ck_project_roles_headcount"),
        CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_project_roles_hours_per_week"),
        CheckConstraint("status IN ('OPEN','CLOSED')", name="ck_project_roles_status"),
    )


class ProjectRoleSkillRow(Base):
    __tablename__ = "project_role_skills"

    role_id: Mapped[str] = mapped_column(String(40), ForeignKey("project_roles.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)
