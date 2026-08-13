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


class AccountDeletionRequestRow(Base):
    __tablename__ = "account_deletion_requests"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    pending_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, unique=True
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_account_deletion_requests_user_requested", "user_id", "requested_at"),
        CheckConstraint("status IN ('PENDING','CANCELLED','COMPLETED')", name="ck_account_deletion_requests_status"),
        CheckConstraint(
            "(status = 'PENDING' AND pending_user_id = user_id) OR "
            "(status <> 'PENDING' AND pending_user_id IS NULL)",
            name="ck_account_deletion_requests_pending_user",
        ),
    )


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_audit_events_actor_created", "actor_user_id", "created_at"),
        Index("ix_audit_events_resource_created", "resource_type", "resource_id", "created_at"),
        Index("ix_audit_events_request", "request_id"),
        CheckConstraint("outcome IN ('SUCCESS','FAILURE')", name="ck_audit_events_outcome"),
    )


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


class InvitationRow(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_id: Mapped[str] = mapped_column(String(40), nullable=False)
    inviter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    invitee_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    pending_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "role_id"],
            ["project_roles.project_id", "project_roles.id"],
            ondelete="RESTRICT",
            name="fk_invitations_project_role",
        ),
        UniqueConstraint("pending_key", name="uq_invitations_pending_key"),
        Index("ix_invitations_invitee_status_expires", "invitee_id", "status", "expires_at"),
        Index("ix_invitations_project_status", "project_id", "status"),
        CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REJECTED','EXPIRED','CANCELLED')",
            name="ck_invitations_status",
        ),
        CheckConstraint("inviter_id <> invitee_id", name="ck_invitations_not_self"),
        CheckConstraint(
            "(status = 'PENDING' AND pending_key IS NOT NULL) OR "
            "(status <> 'PENDING' AND pending_key IS NULL)",
            name="ck_invitations_pending_key",
        ),
    )


class ConversationRow(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    conversation_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_conversations_project_created", "project_id", "created_at", "id"),
    )


class ConversationParticipantRow(Base):
    __tablename__ = "conversation_participants"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_conversation_participants_user_status", "user_id", "status", "conversation_id"),
        CheckConstraint("status IN ('ACTIVE')", name="ck_conversation_participants_status"),
    )


class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(40), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(36), nullable=False)
    client_message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="TEXT")
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="SENT")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["conversation_id", "sender_id"],
            ["conversation_participants.conversation_id", "conversation_participants.user_id"],
            ondelete="RESTRICT",
            name="fk_messages_sender_participant",
        ),
        UniqueConstraint("sender_id", "client_message_id", name="uq_messages_sender_client_id"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at", "id"),
        CheckConstraint("type IN ('TEXT')", name="ck_messages_type"),
        CheckConstraint("status IN ('SENT')", name="ck_messages_status"),
    )


class RecommendationRequestRow(Base):
    __tablename__ = "recommendation_requests"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    viewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    context: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (Index("ix_recommendation_requests_viewer_created", "viewer_user_id", "created_at"),)


class RecommendationCandidateRow(Base):
    __tablename__ = "recommendation_candidates"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("recommendation_requests.id", ondelete="CASCADE"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("request_id", "rank", name="uq_recommendation_candidates_request_rank"),
        UniqueConstraint("request_id", "target_type", "target_id", name="uq_recommendation_candidates_request_target"),
        Index("ix_recommendation_candidates_request_rank", "request_id", "rank"),
    )


class RecommendationImpressionRow(Base):
    __tablename__ = "recommendation_impressions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("recommendation_requests.id", ondelete="CASCADE"), nullable=False)
    viewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    client_occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "request_id", "viewer_user_id", "target_type", "target_id",
            name="uq_recommendation_impressions_request_viewer_target",
        ),
        Index("ix_recommendation_impressions_viewer_received", "viewer_user_id", "received_at"),
    )


class ReportRow(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    pending_key: Mapped[str | None] = mapped_column(String(192), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_reports_status_created", "status", "created_at"),
        Index("ix_reports_target", "target_type", "target_id"),
        CheckConstraint("target_type IN ('USER','PROJECT','MESSAGE')", name="ck_reports_target_type"),
        CheckConstraint(
            "reason IN ('SPAM','HARASSMENT','FRAUD','INAPPROPRIATE_CONTENT','OTHER')",
            name="ck_reports_reason",
        ),
        CheckConstraint("status IN ('PENDING','REVIEWED','DISMISSED','ACTIONED')", name="ck_reports_status"),
        CheckConstraint(
            "(status = 'PENDING' AND pending_key IS NOT NULL) OR "
            "(status <> 'PENDING' AND pending_key IS NULL)",
            name="ck_reports_pending_key",
        ),
    )
