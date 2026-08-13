from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import Engine, Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker

from .db_models import (
    AccountDeletionRequestRow,
    AuditEventRow,
    BlockRow,
    ConversationParticipantRow,
    ConversationRow,
    InvitationRow,
    MatchPreferenceAvailabilitySlotRow,
    MatchPreferenceDirectionRow,
    MatchPreferenceRow,
    MessageRow,
    ProfileRow,
    ProfileScenarioRow,
    ProfileSkillRow,
    ProjectMemberRow,
    ProjectRoleAvailabilitySlotRow,
    ProjectRoleRow,
    ProjectRoleSkillRow,
    ProjectRow,
    ProjectScenarioRow,
    RecommendationCandidateRow,
    RecommendationImpressionRow,
    RecommendationRequestRow,
    ReportRow,
    SessionRow,
    UserRow,
)
from .errors import ServiceError
from .schemas import (
    AccountDeletionRequestData,
    BlockData,
    ConversationData,
    InvitationAcceptData,
    InvitationData,
    MessageData,
    MatchPreferencesData,
    MatchPreferencesPayload,
    ProfileData,
    PublicProfileData,
    MatchResultData,
    ProfilePayload,
    ProjectData,
    ProjectMemberData,
    ProjectPayload,
    ProjectUpdate,
    RoleData,
    RecommendationImpressionData,
    RecommendationImpressionRequest,
    ReportData,
    ReportRequest,
)
from .matching_service import (
    MATCH_SNAPSHOT_TTL,
    MatchSnapshot,
    build_profile_match,
    build_project_match,
    page_snapshot,
    validate_impression_time,
)


def db_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)


def api_datetime(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


class SqlAlchemyStore:
    def __init__(self, session_factory: sessionmaker[Session], engine: Engine) -> None:
        self._session_factory = session_factory
        self._engine = engine
        self._match_snapshots: dict[str, MatchSnapshot] = {}

    def ready(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(select(1))
            return True
        except Exception:
            return False

    def login(self, subject: str) -> tuple[str, str, bool]:
        with self._session_factory() as session:
            user = session.scalar(select(UserRow).where(UserRow.wechat_subject == subject))
            if user is None:
                timestamp = db_now()
                user = UserRow(
                    id=f"usr_{uuid4().hex}",
                    wechat_subject=subject,
                    status="ACTIVE",
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                session.add(user)
                try:
                    session.flush()
                except IntegrityError:
                    session.rollback()
                    user = session.scalar(select(UserRow).where(UserRow.wechat_subject == subject))
                    if user is None:
                        raise ServiceError("INTERNAL_ERROR", "登录状态创建失败。", 500) from None
            if user.status != "ACTIVE":
                raise ServiceError("FORBIDDEN", "当前账号状态不允许登录。", 403)

            token = f"tu_{token_urlsafe(32)}"
            timestamp = db_now()
            session.add(
                SessionRow(
                    id=f"ses_{uuid4().hex}",
                    user_id=user.id,
                    token_digest=token_digest(token),
                    expires_at=timestamp + timedelta(hours=12),
                    revoked_at=None,
                    created_at=timestamp,
                )
            )
            complete = session.get(ProfileRow, user.id) is not None
            session.commit()
            return user.id, token, complete

    def user_for_token(self, token: str) -> str:
        digest = token_digest(token)
        with self._session_factory() as session:
            row = session.scalar(
                select(SessionRow)
                .join(UserRow, UserRow.id == SessionRow.user_id)
                .where(
                    SessionRow.token_digest == digest,
                    SessionRow.revoked_at.is_(None),
                    SessionRow.expires_at > db_now(),
                    UserRow.status == "ACTIVE",
                )
            )
            if row is None:
                raise ServiceError("SESSION_EXPIRED", "登录状态已失效，请重新登录。", 401)
            return row.user_id

    def logout(self, token: str, request_id: str = "req_unknown") -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(select(SessionRow).where(SessionRow.token_digest == token_digest(token)).with_for_update())
            if row is not None and row.revoked_at is None:
                row.revoked_at = db_now()
                self._add_audit_event(session, row.user_id, "LOGOUT", "SESSION", row.id, request_id)

    def request_account_deletion(self, user_id: str, request_id: str) -> AccountDeletionRequestData:
        with self._session_factory.begin() as session:
            user = session.scalar(select(UserRow).where(UserRow.id == user_id).with_for_update())
            if user is None:
                raise ServiceError("SESSION_EXPIRED", "登录状态已失效，请重新登录。", 401)
            existing = session.scalar(
                select(AccountDeletionRequestRow)
                .where(AccountDeletionRequestRow.pending_user_id == user_id)
                .with_for_update()
            )
            if existing is not None:
                return self._account_deletion_request_data(existing)
            if user.status != "ACTIVE":
                raise ServiceError("ACCOUNT_NOT_ACTIVE", "当前账号状态不允许申请注销。", 409)
            timestamp = db_now()
            row = AccountDeletionRequestRow(
                id=f"adrq_{uuid4().hex}",
                user_id=user_id,
                status="PENDING",
                pending_user_id=user_id,
                requested_at=timestamp,
                resolved_at=None,
            )
            session.add(row)
            user.status = "DELETION_PENDING"
            user.updated_at = timestamp
            for active_session in session.scalars(
                select(SessionRow).where(SessionRow.user_id == user_id, SessionRow.revoked_at.is_(None))
            ):
                active_session.revoked_at = timestamp
            session.flush()
            self._add_audit_event(
                session,
                user_id,
                "ACCOUNT_DELETION_REQUESTED",
                "ACCOUNT_DELETION_REQUEST",
                row.id,
                request_id,
            )
            return self._account_deletion_request_data(row)

    @staticmethod
    def _account_deletion_request_data(row: AccountDeletionRequestRow) -> AccountDeletionRequestData:
        return AccountDeletionRequestData(
            id=row.id,
            status=row.status,
            requestedAt=api_datetime(row.requested_at),
        )

    def create_block(self, blocker_id: str, blocked_id: str) -> BlockData:
        if blocker_id == blocked_id:
            raise ServiceError("CANNOT_BLOCK_SELF", "不能拉黑自己。", 422)
        first_id, second_id = sorted((blocker_id, blocked_id))
        with self._session_factory.begin() as session:
            users = list(
                session.scalars(
                    select(UserRow)
                    .where(UserRow.id.in_([first_id, second_id]), UserRow.status == "ACTIVE")
                    .order_by(UserRow.id)
                    .with_for_update()
                )
            )
            if len(users) != 2:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可见。", 404)
            row = session.get(BlockRow, (blocker_id, blocked_id))
            if row is None:
                row = BlockRow(blocker_id=blocker_id, blocked_id=blocked_id, created_at=db_now())
                session.add(row)
                session.flush()
            return BlockData(blockedUserId=blocked_id, createdAt=api_datetime(row.created_at))

    def remove_block(self, blocker_id: str, blocked_id: str) -> bool:
        with self._session_factory.begin() as session:
            row = session.get(BlockRow, (blocker_id, blocked_id), with_for_update=True)
            if row is None:
                return False
            session.delete(row)
            return True

    def users_blocked(self, first_user_id: str, second_user_id: str) -> bool:
        with self._session_factory() as session:
            return self._users_blocked(session, first_user_id, second_user_id)

    def create_report(self, reporter_id: str, payload: ReportRequest, request_id: str) -> ReportData:
        with self._session_factory.begin() as session:
            reporter = session.scalar(
                select(UserRow)
                .where(UserRow.id == reporter_id, UserRow.status == "ACTIVE")
                .with_for_update()
            )
            if reporter is None:
                raise ServiceError("SESSION_EXPIRED", "登录状态已失效，请重新登录。", 401)
            pending_key = f"{reporter_id}:{payload.targetType}:{payload.targetId}:{payload.reason}"
            existing = session.scalar(
                select(ReportRow).where(ReportRow.pending_key == pending_key).with_for_update()
            )
            if existing is not None:
                return self._report_data(existing)
            if not self._report_target_is_visible(session, reporter_id, payload.targetType, payload.targetId):
                raise ServiceError("RESOURCE_NOT_FOUND", "举报目标不存在或不可见。", 404)
            row = ReportRow(
                id=f"rpt_{uuid4().hex}",
                reporter_id=reporter_id,
                target_type=payload.targetType,
                target_id=payload.targetId,
                reason=payload.reason,
                description=payload.description,
                status="PENDING",
                pending_key=pending_key,
                created_at=db_now(),
            )
            session.add(row)
            session.flush()
            self._add_audit_event(
                session, reporter_id, "REPORT_SUBMITTED", "REPORT", row.id, request_id
            )
            return self._report_data(row)

    @staticmethod
    def _add_audit_event(
        session: Session,
        actor_user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        request_id: str,
    ) -> None:
        session.add(
            AuditEventRow(
                id=f"aud_{uuid4().hex}",
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                request_id=request_id,
                outcome="SUCCESS",
                created_at=db_now(),
            )
        )

    @staticmethod
    def _report_data(row: ReportRow) -> ReportData:
        return ReportData(
            id=row.id,
            targetType=row.target_type,
            targetId=row.target_id,
            reason=row.reason,
            status=row.status,
            createdAt=api_datetime(row.created_at),
        )

    @staticmethod
    def _report_target_is_visible(
        session: Session, reporter_id: str, target_type: str, target_id: str
    ) -> bool:
        if target_type == "USER":
            return session.scalar(
                select(UserRow.id).where(
                    UserRow.id == target_id,
                    UserRow.id != reporter_id,
                    UserRow.status == "ACTIVE",
                )
            ) is not None
        if target_type == "PROJECT":
            return session.scalar(
                select(ProjectRow.id)
                .join(UserRow, UserRow.id == ProjectRow.owner_id)
                .where(
                    ProjectRow.id == target_id,
                    ProjectRow.owner_id != reporter_id,
                    ProjectRow.status == "PUBLISHED",
                    UserRow.status == "ACTIVE",
                )
            ) is not None
        if target_type == "MESSAGE":
            message = session.scalar(select(MessageRow).where(MessageRow.id == target_id))
            if message is None:
                return False
            participant = session.scalar(
                select(ConversationParticipantRow.user_id).where(
                    ConversationParticipantRow.conversation_id == message.conversation_id,
                    ConversationParticipantRow.user_id == reporter_id,
                    ConversationParticipantRow.status == "ACTIVE",
                )
            )
            return participant is not None and message.sender_id != reporter_id
        return False

    def create_invitation(
        self, inviter_id: str, project_id: str, role_id: str, invitee_id: str
    ) -> InvitationData:
        with self._session_factory.begin() as session:
            project = session.scalar(select(ProjectRow).where(ProjectRow.id == project_id).with_for_update())
            self._require_owner(project, inviter_id)
            if inviter_id == invitee_id:
                raise ServiceError("CANNOT_INVITE_SELF", "不能邀请自己加入项目。", 422)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许创建邀请。", 409)
            users = list(
                session.scalars(
                    select(UserRow)
                    .where(UserRow.id.in_(sorted((inviter_id, invitee_id))))
                    .order_by(UserRow.id)
                    .with_for_update()
                )
            )
            invitee = next((item for item in users if item.id == invitee_id and item.status == "ACTIVE"), None)
            if invitee is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可见。", 404)
            if self._users_blocked(session, inviter_id, invitee_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许创建邀请。", 409)
            role = session.scalar(
                select(ProjectRoleRow)
                .where(ProjectRoleRow.id == role_id, ProjectRoleRow.project_id == project_id)
                .with_for_update()
            )
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            self._require_open_role_capacity(session, role)
            if self._active_member(session, project_id, invitee_id) is not None:
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409)

            timestamp = db_now()
            pending_key = self._invitation_pending_key(project_id, role_id, invitee_id)
            existing = session.scalar(
                select(InvitationRow).where(InvitationRow.pending_key == pending_key).with_for_update()
            )
            if existing is not None and existing.expires_at > timestamp:
                return self._invitation_data(existing)
            if existing is not None:
                existing.status = "EXPIRED"
                existing.pending_key = None
                existing.responded_at = timestamp
                session.flush()

            row = InvitationRow(
                id=f"inv_{uuid4().hex}",
                project_id=project_id,
                role_id=role_id,
                inviter_id=inviter_id,
                invitee_id=invitee_id,
                status="PENDING",
                pending_key=pending_key,
                expires_at=timestamp + timedelta(days=7),
                created_at=timestamp,
                responded_at=None,
            )
            session.add(row)
            session.flush()
            return self._invitation_data(row)

    def accept_invitation(self, invitee_id: str, invitation_id: str) -> InvitationAcceptData:
        # Locate the project outside the write transaction. On MySQL REPEATABLE READ,
        # a normal read before the project lock would freeze an obsolete capacity snapshot.
        with self._session_factory() as lookup_session:
            visible = lookup_session.get(InvitationRow, invitation_id)
            if visible is None or visible.invitee_id != invitee_id:
                raise ServiceError("RESOURCE_NOT_FOUND", "邀请不存在或不可见。", 404)
            project_id = visible.project_id
            role_id = visible.role_id
        with self._session_factory.begin() as session:
            project = session.scalar(
                select(ProjectRow).where(ProjectRow.id == project_id).with_for_update()
            )
            if project is None:
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可接受。", 409)
            users = list(
                session.scalars(
                    select(UserRow)
                    .where(UserRow.id.in_(sorted((project.owner_id, invitee_id))))
                    .order_by(UserRow.id)
                    .with_for_update()
                )
            )
            role = session.scalar(
                select(ProjectRoleRow)
                .where(ProjectRoleRow.id == role_id, ProjectRoleRow.project_id == project.id)
                .with_for_update()
            )
            invitation = session.scalar(
                select(InvitationRow)
                .where(InvitationRow.id == invitation_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            if invitation is None or invitation.invitee_id != invitee_id:
                raise ServiceError("RESOURCE_NOT_FOUND", "邀请不存在或不可见。", 404)
            if invitation.status == "ACCEPTED":
                member = self._active_member(session, invitation.project_id, invitee_id)
                if member is None or role is None:
                    raise ServiceError("INTERNAL_ERROR", "邀请成员状态不一致。", 500)
                return InvitationAcceptData(
                    invitation=self._invitation_data(invitation),
                    member=self._project_member_data(member, role.name),
                )
            timestamp = db_now()
            if invitation.status != "PENDING" or invitation.expires_at <= timestamp:
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可接受。", 409)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许接受邀请。", 409)
            candidate = next((item for item in users if item.id == invitee_id and item.status == "ACTIVE"), None)
            if candidate is None:
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可接受。", 409)
            if self._users_blocked(session, project.owner_id, invitee_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许接受邀请。", 409)
            if role is None:
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可接受。", 409)
            self._require_open_role_capacity(session, role)
            if self._active_member(session, project.id, invitee_id) is not None:
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409)

            member = ProjectMemberRow(
                id=f"mem_{uuid4().hex}",
                project_id=project.id,
                role_id=role.id,
                user_id=invitee_id,
                status="ACTIVE",
                joined_at=timestamp,
            )
            invitation.status = "ACCEPTED"
            invitation.pending_key = None
            invitation.responded_at = timestamp
            session.add(member)
            session.flush()
            return InvitationAcceptData(
                invitation=self._invitation_data(invitation),
                member=self._project_member_data(member, role.name),
            )

    def reject_invitation(self, invitee_id: str, invitation_id: str) -> InvitationData:
        with self._session_factory.begin() as session:
            invitation = session.scalar(
                select(InvitationRow).where(InvitationRow.id == invitation_id).with_for_update()
            )
            if invitation is None or invitation.invitee_id != invitee_id:
                raise ServiceError("RESOURCE_NOT_FOUND", "邀请不存在或不可见。", 404)
            if invitation.status == "REJECTED":
                return self._invitation_data(invitation)
            timestamp = db_now()
            if invitation.status != "PENDING" or invitation.expires_at <= timestamp:
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可拒绝。", 409)
            invitation.status = "REJECTED"
            invitation.pending_key = None
            invitation.responded_at = timestamp
            session.flush()
            return self._invitation_data(invitation)

    def create_conversation(
        self, requester_id: str, project_id: str, other_user_id: str
    ) -> ConversationData:
        if requester_id == other_user_id:
            raise ServiceError("CANNOT_MESSAGE_SELF", "不能与自己创建会话。", 422)
        with self._session_factory.begin() as session:
            project = session.scalar(select(ProjectRow).where(ProjectRow.id == project_id).with_for_update())
            if project is None or project.status != "PUBLISHED":
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可联系。", 404)
            participant_ids = sorted((requester_id, other_user_id))
            users = list(
                session.scalars(
                    select(UserRow)
                    .where(UserRow.id.in_(participant_ids), UserRow.status == "ACTIVE")
                    .order_by(UserRow.id)
                    .with_for_update()
                )
            )
            if len(users) != 2:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可联系。", 404)
            related_user_ids = {project.owner_id}
            related_user_ids.update(
                session.scalars(
                    select(ProjectMemberRow.user_id).where(
                        ProjectMemberRow.project_id == project_id,
                        ProjectMemberRow.user_id.in_(participant_ids),
                        ProjectMemberRow.status == "ACTIVE",
                    )
                )
            )
            if not (set(participant_ids) & related_user_ids):
                raise ServiceError("FORBIDDEN", "当前用户关系不能基于该项目创建会话。", 403)
            if self._users_blocked(session, requester_id, other_user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许创建会话。", 409)
            conversation_key = self._conversation_key(project_id, participant_ids)
            existing = session.scalar(
                select(ConversationRow)
                .where(ConversationRow.conversation_key == conversation_key)
                .with_for_update()
            )
            if existing is not None:
                return self._conversation_data(session, existing)
            timestamp = db_now()
            row = ConversationRow(
                id=f"con_{uuid4().hex}",
                project_id=project_id,
                conversation_key=conversation_key,
                last_message_at=None,
                created_at=timestamp,
            )
            session.add(row)
            session.flush()
            session.add_all(
                [
                    ConversationParticipantRow(
                        conversation_id=row.id,
                        user_id=user_id,
                        status="ACTIVE",
                        joined_at=timestamp,
                    )
                    for user_id in participant_ids
                ]
            )
            session.flush()
            return self._conversation_data(session, row)

    def list_conversations(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[ConversationData], str | None]:
        with self._session_factory() as session:
            sort_time = func.coalesce(ConversationRow.last_message_at, ConversationRow.created_at)
            query = (
                select(ConversationRow)
                .join(
                    ConversationParticipantRow,
                    ConversationParticipantRow.conversation_id == ConversationRow.id,
                )
                .where(
                    ConversationParticipantRow.user_id == requester_id,
                    ConversationParticipantRow.status == "ACTIVE",
                )
            )
            if cursor:
                cursor_time, cursor_id = self._decode_cursor(cursor)
                query = query.where(
                    or_(sort_time < cursor_time, (sort_time == cursor_time) & (ConversationRow.id < cursor_id))
                )
            rows = list(session.scalars(query.order_by(sort_time.desc(), ConversationRow.id.desc()).limit(limit + 1)))
            has_more = len(rows) > limit
            page = rows[:limit]
            data = [self._conversation_data(session, row) for row in page]
            next_cursor = (
                self._encode_cursor(page[-1].last_message_at or page[-1].created_at, page[-1].id)
                if has_more and page
                else None
            )
            return data, next_cursor

    def list_messages(
        self, requester_id: str, conversation_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MessageData], str | None]:
        with self._session_factory() as session:
            self._require_conversation_participant(session, conversation_id, requester_id)
            query = select(MessageRow).where(MessageRow.conversation_id == conversation_id)
            if cursor:
                cursor_time, cursor_id = self._decode_cursor(cursor)
                query = query.where(
                    or_(
                        MessageRow.created_at > cursor_time,
                        (MessageRow.created_at == cursor_time) & (MessageRow.id > cursor_id),
                    )
                )
            rows = list(session.scalars(query.order_by(MessageRow.created_at, MessageRow.id).limit(limit + 1)))
            has_more = len(rows) > limit
            page = rows[:limit]
            return [self._message_data(row) for row in page], (
                self._encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
            )

    def send_message(
        self, requester_id: str, conversation_id: str, client_message_id: str, content: str
    ) -> MessageData:
        with self._session_factory.begin() as session:
            conversation = session.scalar(
                select(ConversationRow).where(ConversationRow.id == conversation_id).with_for_update()
            )
            if conversation is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "会话不存在或不可见。", 404)
            participant_ids = list(
                session.scalars(
                    select(ConversationParticipantRow.user_id)
                    .where(
                        ConversationParticipantRow.conversation_id == conversation_id,
                        ConversationParticipantRow.status == "ACTIVE",
                    )
                    .order_by(ConversationParticipantRow.user_id)
                )
            )
            if requester_id not in participant_ids or len(participant_ids) != 2:
                raise ServiceError("RESOURCE_NOT_FOUND", "会话不存在或不可见。", 404)
            existing = session.scalar(
                select(MessageRow).where(
                    MessageRow.sender_id == requester_id,
                    MessageRow.client_message_id == client_message_id,
                )
            )
            if existing is not None:
                if existing.conversation_id != conversation_id or existing.content != content:
                    raise ServiceError(
                        "MESSAGE_IDEMPOTENCY_CONFLICT", "消息幂等键已用于不同内容。", 409
                    )
                return self._message_data(existing)
            other_user_id = next(item for item in participant_ids if item != requester_id)
            if self._users_blocked(session, requester_id, other_user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许发送消息。", 409)
            timestamp = db_now()
            row = MessageRow(
                id=f"msg_{uuid4().hex}",
                conversation_id=conversation_id,
                sender_id=requester_id,
                client_message_id=client_message_id,
                type="TEXT",
                content=content,
                status="SENT",
                created_at=timestamp,
            )
            conversation.last_message_at = timestamp
            session.add(row)
            try:
                session.flush()
            except IntegrityError:
                raise ServiceError(
                    "MESSAGE_IDEMPOTENCY_CONFLICT", "消息幂等键已用于其他请求。", 409
                ) from None
            return self._message_data(row)

    def get_profile(self, user_id: str) -> ProfileData | None:
        with self._session_factory() as session:
            row = session.scalar(self._profile_query().where(ProfileRow.user_id == user_id))
            return self._profile_data(row) if row else None

    def get_public_profile(self, requester_id: str, user_id: str) -> PublicProfileData:
        with self._session_factory() as session:
            if requester_id == user_id:
                raise ServiceError("RESOURCE_NOT_FOUND", "公开名片不存在或不可见。", 404)
            user = session.scalar(select(UserRow).where(UserRow.id == user_id, UserRow.status == "ACTIVE"))
            row = session.scalar(self._profile_query().where(ProfileRow.user_id == user_id, ProfileRow.visibility.is_(True)))
            if user is None or row is None or self._users_blocked(session, requester_id, user_id):
                raise ServiceError("RESOURCE_NOT_FOUND", "公开名片不存在或不可见。", 404)
            return self._public_profile_data(user_id, row)

    def list_public_profiles(
        self,
        requester_id: str,
        limit: int,
        cursor: str | None,
        skill: str | None,
        direction: str | None,
        collaboration_role: str | None,
        min_hours_per_week: int | None,
        max_hours_per_week: int | None,
    ) -> tuple[list[PublicProfileData], str | None]:
        with self._session_factory() as session:
            query = self._profile_query().join(UserRow, UserRow.id == ProfileRow.user_id).where(
                ProfileRow.visibility.is_(True), UserRow.status == "ACTIVE", ProfileRow.user_id != requester_id
            )
            if skill:
                query = query.join(ProfileSkillRow, ProfileSkillRow.user_id == ProfileRow.user_id).where(
                    func.lower(ProfileSkillRow.skill_name) == skill.casefold()
                )
            if direction:
                query = query.join(MatchPreferenceRow, MatchPreferenceRow.user_id == ProfileRow.user_id).join(
                    MatchPreferenceDirectionRow, MatchPreferenceDirectionRow.user_id == MatchPreferenceRow.user_id
                ).where(func.lower(MatchPreferenceDirectionRow.direction_code) == direction.casefold())
            if collaboration_role:
                query = query.where(ProfileRow.role_preference == collaboration_role)
            if min_hours_per_week is not None:
                query = query.where(ProfileRow.hours_per_week >= min_hours_per_week)
            if max_hours_per_week is not None:
                query = query.where(ProfileRow.hours_per_week <= max_hours_per_week)
            rows = [row for row in session.scalars(query).unique() if not self._users_blocked(session, requester_id, row.user_id)]
            rows.sort(key=lambda row: (row.updated_at, row.user_id), reverse=True)
            ids = [row.user_id for row in rows]
            if cursor:
                if cursor not in ids:
                    raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422)
                rows = rows[ids.index(cursor) + 1 :]
            page = rows[:limit]
            return [self._public_profile_data(row.user_id, row) for row in page], page[-1].user_id if len(rows) > limit and page else None

    def save_profile(self, user_id: str, payload: ProfilePayload, version: int | None) -> ProfileData:
        with self._session_factory.begin() as session:
            user = session.scalar(select(UserRow).where(UserRow.id == user_id).with_for_update())
            if user is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            row = session.scalar(self._profile_query().where(ProfileRow.user_id == user_id).with_for_update())
            if row and version != row.version:
                raise ServiceError("VERSION_CONFLICT", "能力名片已被更新，请重新加载后再保存。", 409)
            if not row and version not in (None, 0):
                raise ServiceError("VERSION_CONFLICT", "能力名片版本已失效，请重新加载。", 409)

            timestamp = db_now()
            if row is None:
                row = ProfileRow(user_id=user_id, version=1, updated_at=timestamp)
                session.add(row)
            else:
                row.version += 1
                row.updated_at = timestamp
            self._apply_profile(row, payload)
            session.flush()
            return self._profile_data(row)

    def get_match_preferences(self, user_id: str) -> MatchPreferencesData | None:
        with self._session_factory() as session:
            row = session.scalar(self._match_preferences_query().where(MatchPreferenceRow.user_id == user_id))
            return self._match_preferences_data(row) if row else None

    def save_match_preferences(
        self,
        user_id: str,
        payload: MatchPreferencesPayload,
        version: int | None,
    ) -> MatchPreferencesData:
        with self._session_factory.begin() as session:
            user = session.scalar(select(UserRow).where(UserRow.id == user_id).with_for_update())
            if user is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            row = session.scalar(
                self._match_preferences_query()
                .where(MatchPreferenceRow.user_id == user_id)
                .with_for_update()
            )
            if row and version != row.version:
                raise ServiceError("VERSION_CONFLICT", "匹配偏好已被更新，请重新加载后再保存。", 409)
            if not row and version not in (None, 0):
                raise ServiceError("VERSION_CONFLICT", "匹配偏好版本已失效，请重新加载。", 409)

            timestamp = db_now()
            if row is None:
                row = MatchPreferenceRow(user_id=user_id, version=1, updated_at=timestamp)
                session.add(row)
            else:
                row.version += 1
                row.updated_at = timestamp
            self._apply_match_preferences(row, payload)
            session.flush()
            return self._match_preferences_data(row)

    def create_project(self, user_id: str, payload: ProjectPayload) -> ProjectData:
        with self._session_factory.begin() as session:
            if session.get(UserRow, user_id) is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            timestamp = db_now()
            row = ProjectRow(
                id=f"prj_{uuid4().hex}",
                owner_id=user_id,
                title=payload.title,
                description=payload.description,
                direction=payload.direction,
                competition=payload.competition,
                stage=payload.stage,
                team_info=payload.teamInfo,
                status="DRAFT",
                version=1,
                published_at=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
            self._replace_roles(row, payload.roles)
            self._replace_project_scenarios(row, payload.collaborationScenarios or [])
            session.add(row)
            session.flush()
            return self._project_data(row)

    def get_project(self, project_id: str, requester_id: str | None = None) -> ProjectData:
        with self._session_factory() as session:
            row = session.scalar(self._project_query().where(ProjectRow.id == project_id))
            if row is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            if requester_id is not None and row.owner_id != requester_id:
                owner = session.scalar(
                    select(UserRow).where(UserRow.id == row.owner_id, UserRow.status == "ACTIVE")
                )
                if (
                    row.status == "DRAFT"
                    or owner is None
                    or self._users_blocked(session, requester_id, row.owner_id)
                ):
                    raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            return self._project_data(row)

    def update_project(self, user_id: str, project_id: str, payload: ProjectUpdate) -> ProjectData:
        with self._session_factory.begin() as session:
            row = session.scalar(self._project_query().where(ProjectRow.id == project_id).with_for_update())
            self._require_owner(row, user_id)
            if row.status != "DRAFT":
                raise ServiceError("PROJECT_NOT_EDITABLE", "项目当前状态不可编辑。", 409)
            if payload.version != row.version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再保存。", 409)
            row.title = payload.title
            row.description = payload.description
            row.direction = payload.direction
            row.competition = payload.competition
            row.stage = payload.stage
            row.team_info = payload.teamInfo
            row.version += 1
            row.updated_at = db_now()
            existing_roles = self._project_data(row).roles
            row.roles.clear()
            session.flush()
            self._replace_roles(row, payload.roles, existing_roles)
            if payload.collaborationScenarios is not None:
                self._replace_project_scenarios(row, payload.collaborationScenarios)
            session.flush()
            return self._project_data(row)

    def publish_project(self, user_id: str, project_id: str, version: int) -> ProjectData:
        with self._session_factory.begin() as session:
            row = session.scalar(self._project_query().where(ProjectRow.id == project_id).with_for_update())
            self._require_owner(row, user_id)
            if row.status != "DRAFT":
                raise ServiceError("PROJECT_NOT_PUBLISHABLE", "项目当前状态不可发布。", 409)
            if row.version != version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再发布。", 409)
            if not any(role.status == "OPEN" for role in row.roles):
                raise ServiceError("PROJECT_NOT_PUBLISHABLE", "至少需要一个开放岗位才能发布。", 409)
            timestamp = db_now()
            row.status = "PUBLISHED"
            row.version += 1
            row.published_at = timestamp
            row.updated_at = timestamp
            session.flush()
            return self._project_data(row)

    def close_project(self, user_id: str, project_id: str, version: int) -> ProjectData:
        with self._session_factory.begin() as session:
            row = session.scalar(self._project_query().where(ProjectRow.id == project_id).with_for_update())
            self._require_owner(row, user_id)
            if row.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_CLOSABLE", "只有已发布项目可以关闭。", 409)
            if row.version != version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再关闭。", 409)
            row.status = "CLOSED"
            row.version += 1
            row.updated_at = db_now()
            session.flush()
            return self._project_data(row)

    def add_project_member(self, project_id: str, role_id: str, user_id: str) -> ProjectMemberData:
        with self._session_factory.begin() as session:
            project = session.scalar(select(ProjectRow).where(ProjectRow.id == project_id).with_for_update())
            if project is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许新增成员。", 409)
            user_ids = sorted((project.owner_id, user_id))
            users = list(
                session.scalars(
                    select(UserRow).where(UserRow.id.in_(user_ids)).order_by(UserRow.id).with_for_update()
                )
            )
            candidate = next((item for item in users if item.id == user_id and item.status == "ACTIVE"), None)
            if candidate is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            if self._users_blocked(session, project.owner_id, user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许新增成员。", 409)
            role = session.scalar(
                select(ProjectRoleRow)
                .where(ProjectRoleRow.id == role_id, ProjectRoleRow.project_id == project_id)
                .with_for_update()
            )
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if role.status != "OPEN":
                raise ServiceError("ROLE_NOT_OPEN", "岗位当前不接受新成员。", 409)
            existing = session.scalar(
                select(ProjectMemberRow).where(
                    ProjectMemberRow.project_id == project_id,
                    ProjectMemberRow.user_id == user_id,
                    ProjectMemberRow.status == "ACTIVE",
                )
            )
            if existing is not None:
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409)
            filled_count = session.scalar(
                select(func.count(ProjectMemberRow.id)).where(
                    ProjectMemberRow.role_id == role_id,
                    ProjectMemberRow.status == "ACTIVE",
                )
            )
            if (filled_count or 0) >= role.headcount:
                raise ServiceError("ROLE_FULL", "岗位容量已满。", 409)

            member = ProjectMemberRow(
                id=f"mem_{uuid4().hex}",
                project_id=project_id,
                role_id=role_id,
                user_id=user_id,
                status="ACTIVE",
                joined_at=db_now(),
            )
            session.add(member)
            try:
                session.flush()
            except IntegrityError:
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409) from None
            return self._project_member_data(member, role.name)

    def list_project_members(self, requester_id: str, project_id: str) -> list[ProjectMemberData]:
        with self._session_factory() as session:
            project = session.scalar(self._project_query().where(ProjectRow.id == project_id))
            if project is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            active_members = [member for member in project.members if member.status == "ACTIVE"]
            if project.owner_id != requester_id and not any(
                member.user_id == requester_id for member in active_members
            ):
                raise ServiceError("FORBIDDEN", "你没有权限查看该项目成员。", 403)
            role_names = {role.id: role.name for role in project.roles}
            return [
                self._project_member_data(member, role_names[member.role_id])
                for member in sorted(active_members, key=lambda item: (item.joined_at, item.id))
            ]

    def list_projects(
        self,
        status: str,
        limit: int,
        cursor: str | None,
        direction: str | None = None,
        competition: str | None = None,
        stage: str | None = None,
        skill: str | None = None,
        requester_id: str | None = None,
    ) -> tuple[list[ProjectData], str | None]:
        with self._session_factory() as session:
            sort_time = func.coalesce(ProjectRow.published_at, ProjectRow.created_at)
            query = self._project_query().join(UserRow, UserRow.id == ProjectRow.owner_id).where(
                ProjectRow.status == status, UserRow.status == "ACTIVE"
            )
            if requester_id:
                blocked_owner = select(BlockRow.blocker_id).where(
                    or_(
                        (BlockRow.blocker_id == requester_id) & (BlockRow.blocked_id == ProjectRow.owner_id),
                        (BlockRow.blocker_id == ProjectRow.owner_id) & (BlockRow.blocked_id == requester_id),
                    )
                ).exists()
                query = query.where(~blocked_owner)
            if direction:
                query = query.where(func.lower(ProjectRow.direction) == direction.casefold())
            if competition:
                query = query.where(func.lower(ProjectRow.competition) == competition.casefold())
            if stage:
                query = query.where(func.lower(ProjectRow.stage) == stage.casefold())
            if skill:
                query = query.join(ProjectRoleRow, ProjectRoleRow.project_id == ProjectRow.id).join(
                    ProjectRoleSkillRow, ProjectRoleSkillRow.role_id == ProjectRoleRow.id
                ).where(func.lower(ProjectRoleSkillRow.skill_name) == skill.casefold())
            if cursor:
                cursor_row = session.scalar(select(ProjectRow).where(ProjectRow.id == cursor))
                if cursor_row is None or cursor_row.status != status:
                    raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422)
                cursor_time = cursor_row.published_at or cursor_row.created_at
                query = query.where(
                    or_(sort_time < cursor_time, (sort_time == cursor_time) & (ProjectRow.id < cursor_row.id))
                )
            rows = list(session.scalars(query.order_by(sort_time.desc(), ProjectRow.id.desc()).limit(limit + 1)).unique())
            has_more = len(rows) > limit
            page = rows[:limit]
            return [self._project_data(row) for row in page], (page[-1].id if has_more and page else None)

    def list_my_projects(
        self, user_id: str, status: str | None, limit: int, cursor: str | None
    ) -> tuple[list[ProjectData], str | None]:
        with self._session_factory() as session:
            query = self._project_query().where(ProjectRow.owner_id == user_id)
            if status:
                query = query.where(ProjectRow.status == status)
            rows = list(session.scalars(query).unique())
            rows.sort(key=lambda row: (row.updated_at, row.id), reverse=True)
            ids = [row.id for row in rows]
            if cursor:
                if cursor not in ids:
                    raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422)
                rows = rows[ids.index(cursor) + 1 :]
            page = rows[:limit]
            return [self._project_data(row) for row in page], page[-1].id if len(rows) > limit and page else None

    def project_matches(
        self, requester_id: str, project_id: str, role_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]:
        with self._session_factory() as session:
            project = session.scalar(self._project_query().where(ProjectRow.id == project_id))
            if project is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            if project.owner_id != requester_id:
                raise ServiceError("FORBIDDEN", "你没有权限查看该项目匹配。", 403)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许匹配。", 409)
            role = next((item for item in project.roles if item.id == role_id), None)
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            project_data = self._project_data(project)
            role_data = next(item for item in project_data.roles if item.id == role_id)
            if role_data.status != "OPEN" or role_data.remainingCount <= 0:
                raise ServiceError("PROJECT_NOT_MATCHABLE", "岗位当前不允许匹配。", 409)
            results: list[MatchResultData] = []
            member_ids = {
                item.user_id for item in project.members if item.project_id == project_id and item.status == "ACTIVE"
            }
            profiles = list(session.scalars(self._profile_query().join(UserRow, UserRow.id == ProfileRow.user_id).where(
                ProfileRow.visibility.is_(True), UserRow.status == "ACTIVE"
            )).unique())
            for profile_row in profiles:
                candidate_id = profile_row.user_id
                if candidate_id == requester_id or candidate_id in member_ids or self._users_blocked(session, requester_id, candidate_id):
                    continue
                profile = self._profile_data(profile_row)
                preferences_row = session.scalar(self._match_preferences_query().where(MatchPreferenceRow.user_id == candidate_id))
                preferences = self._match_preferences_data(preferences_row) if preferences_row else None
                result = build_profile_match(project_data, role_data, candidate_id, profile, preferences)
                if result is not None:
                    results.append(result)
            results.sort(key=lambda item: (-item.score, item.targetId))
            context = f"project:{requester_id}:{project_id}:{role_id}"
            page, next_cursor, request_id = page_snapshot(
                self._match_snapshots, context, results, limit, cursor, viewer_user_id=requester_id
            )
            if cursor is None:
                self._persist_recommendation_snapshot(session, requester_id, context, request_id, results)
            session.commit()
            return page, next_cursor, request_id

    def user_project_matches(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]:
        with self._session_factory() as session:
            profile_row = session.scalar(self._profile_query().where(ProfileRow.user_id == requester_id))
            if profile_row is None:
                raise ServiceError("MATCH_PROFILE_INCOMPLETE", "请先完成能力名片后再匹配。", 409)
            preferences_row = session.scalar(self._match_preferences_query().where(MatchPreferenceRow.user_id == requester_id))
            if preferences_row is None:
                raise ServiceError("MATCH_PROFILE_INCOMPLETE", "请先完善匹配偏好后再匹配。", 409)
            profile = self._profile_data(profile_row)
            preferences = self._match_preferences_data(preferences_row)
            results: list[MatchResultData] = []
            projects = list(
                session.scalars(
                    self._project_query()
                    .join(UserRow, UserRow.id == ProjectRow.owner_id)
                    .where(ProjectRow.status == "PUBLISHED", UserRow.status == "ACTIVE")
                ).unique()
            )
            for project in projects:
                if project.owner_id == requester_id or self._users_blocked(session, requester_id, project.owner_id):
                    continue
                project_data = self._project_data(project)
                if any(item.user_id == requester_id and item.status == "ACTIVE" for item in project.members):
                    continue
                for role in project_data.roles:
                    result = build_project_match(requester_id, profile, preferences, project_data, role)
                    if result is not None:
                        results.append(result)
            results.sort(key=lambda item: (-item.score, item.targetId))
            context = f"user:{requester_id}"
            page, next_cursor, request_id = page_snapshot(
                self._match_snapshots, context, results, limit, cursor, viewer_user_id=requester_id
            )
            if cursor is None:
                self._persist_recommendation_snapshot(session, requester_id, context, request_id, results)
            session.commit()
            return page, next_cursor, request_id

    def record_recommendation_impressions(
        self, requester_id: str, payload: RecommendationImpressionRequest
    ) -> list[RecommendationImpressionData]:
        with self._session_factory.begin() as session:
            request_row = session.scalar(
                select(RecommendationRequestRow)
                .where(RecommendationRequestRow.id == payload.recommendationRequestId)
                .with_for_update()
            )
            if request_row is None or request_row.viewer_user_id != requester_id:
                raise ServiceError("RECOMMENDATION_REQUEST_INVALID", "推荐请求不存在或不可见。", 422)
            now = db_now()
            if request_row.expires_at <= now:
                raise ServiceError("RECOMMENDATION_EXPIRED", "推荐请求已过期，请重新加载。", 410)
            occurred_at = validate_impression_time(payload.occurredAt, now.replace(tzinfo=UTC))
            candidates = {
                (row.target_type, row.target_id)
                for row in session.scalars(
                    select(RecommendationCandidateRow).where(
                        RecommendationCandidateRow.request_id == payload.recommendationRequestId
                    )
                )
            }
            for item in payload.items:
                if (item.targetType, item.targetId) not in candidates:
                    raise ServiceError("INVALID_RECOMMENDATION_TARGET", "曝光候选不属于该推荐请求。", 422)
                if not self._impression_target_is_currently_valid(
                    session, requester_id, request_row.context, item.targetType, item.targetId
                ):
                    raise ServiceError("INVALID_RECOMMENDATION_TARGET", "曝光候选当前已不可见。", 422)
            existing_rows = {
                (row.target_type, row.target_id): row
                for row in session.scalars(
                    select(RecommendationImpressionRow).where(
                        RecommendationImpressionRow.request_id == payload.recommendationRequestId,
                        RecommendationImpressionRow.viewer_user_id == requester_id,
                    )
                )
            }
            for item in payload.items:
                existing = existing_rows.get((item.targetType, item.targetId))
                if existing is not None and existing.position != item.position:
                    raise ServiceError("IMPRESSION_CONFLICT", "同一候选的曝光位置不能变更。", 409)
            recorded: list[RecommendationImpressionData] = []
            for item in payload.items:
                existing = existing_rows.get((item.targetType, item.targetId))
                if existing is not None:
                    recorded.append(
                        RecommendationImpressionData(
                            recommendationRequestId=payload.recommendationRequestId,
                            targetType=item.targetType,
                            targetId=item.targetId,
                            position=existing.position,
                            recordedAt=api_datetime(existing.received_at),
                            duplicate=True,
                        )
                    )
                    continue
                row = RecommendationImpressionRow(
                    id=f"rim_{uuid4().hex}",
                    request_id=payload.recommendationRequestId,
                    viewer_user_id=requester_id,
                    target_type=item.targetType,
                    target_id=item.targetId,
                    position=item.position,
                    client_occurred_at=occurred_at.replace(tzinfo=None),
                    received_at=now,
                )
                session.add(row)
                recorded.append(
                    RecommendationImpressionData(
                        recommendationRequestId=payload.recommendationRequestId,
                        targetType=item.targetType,
                        targetId=item.targetId,
                        position=item.position,
                        recordedAt=api_datetime(now),
                        duplicate=False,
                    )
                )
            session.flush()
            return recorded

    @staticmethod
    def _persist_recommendation_snapshot(
        session: Session,
        requester_id: str,
        context: str,
        request_id: str,
        results: list[MatchResultData],
    ) -> None:
        timestamp = db_now()
        session.add(
            RecommendationRequestRow(
                id=request_id,
                viewer_user_id=requester_id,
                context=context,
                expires_at=timestamp + MATCH_SNAPSHOT_TTL,
                created_at=timestamp,
            )
        )
        # These rows use scalar foreign keys rather than ORM relationships, so
        # SQLAlchemy cannot infer the parent-before-child insert dependency.
        session.flush()
        session.add_all(
            RecommendationCandidateRow(
                id=f"rc_{uuid4().hex}",
                request_id=request_id,
                rank=rank,
                target_type=result.targetType,
                target_id=result.targetId,
            )
            for rank, result in enumerate(results, start=1)
        )

    def _impression_target_is_currently_valid(
        self,
        session: Session,
        requester_id: str,
        context: str,
        target_type: str,
        target_id: str,
    ) -> bool:
        parts = context.split(":")
        if parts[0] == "project" and len(parts) == 4 and target_type == "PROFILE":
            _, owner_id, project_id, role_id = parts
            project = session.scalar(select(ProjectRow).where(ProjectRow.id == project_id))
            role = session.scalar(
                select(ProjectRoleRow).where(ProjectRoleRow.project_id == project_id, ProjectRoleRow.id == role_id)
            )
            profile = session.scalar(
                select(ProfileRow)
                .join(UserRow, UserRow.id == ProfileRow.user_id)
                .where(
                    ProfileRow.user_id == target_id,
                    ProfileRow.visibility.is_(True),
                    UserRow.status == "ACTIVE",
                )
            )
            member = self._active_member(session, project_id, target_id)
            filled_count = session.scalar(
                select(func.count(ProjectMemberRow.id)).where(
                    ProjectMemberRow.role_id == role_id, ProjectMemberRow.status == "ACTIVE"
                )
            )
            return bool(
                owner_id == requester_id
                and project is not None
                and project.status == "PUBLISHED"
                and role is not None
                and role.status == "OPEN"
                and (filled_count or 0) < role.headcount
                and profile is not None
                and target_id != requester_id
                and member is None
                and not self._users_blocked(session, requester_id, target_id)
            )
        if parts[0] == "user" and len(parts) == 2 and target_type == "PROJECT_ROLE":
            role = session.scalar(select(ProjectRoleRow).where(ProjectRoleRow.id == target_id))
            if role is None:
                return False
            project = session.scalar(select(ProjectRow).where(ProjectRow.id == role.project_id))
            owner_active = (
                session.scalar(
                    select(UserRow.id).where(
                        UserRow.id == project.owner_id,
                        UserRow.status == "ACTIVE",
                    )
                )
                if project is not None
                else None
            )
            filled_count = session.scalar(
                select(func.count(ProjectMemberRow.id)).where(
                    ProjectMemberRow.role_id == role.id, ProjectMemberRow.status == "ACTIVE"
                )
            )
            return bool(
                project is not None
                and owner_active is not None
                and project.status == "PUBLISHED"
                and role.status == "OPEN"
                and (filled_count or 0) < role.headcount
                and project.owner_id != requester_id
                and self._active_member(session, project.id, requester_id) is None
                and not self._users_blocked(session, requester_id, project.owner_id)
            )
        return False

    @staticmethod
    def _profile_query() -> Select[tuple[ProfileRow]]:
        return select(ProfileRow).options(selectinload(ProfileRow.skills), selectinload(ProfileRow.scenarios))

    @staticmethod
    def _users_blocked(session: Session, first_user_id: str, second_user_id: str) -> bool:
        return (
            session.scalar(
                select(BlockRow.blocker_id).where(
                    or_(
                        (BlockRow.blocker_id == first_user_id) & (BlockRow.blocked_id == second_user_id),
                        (BlockRow.blocker_id == second_user_id) & (BlockRow.blocked_id == first_user_id),
                    )
                )
            )
            is not None
        )

    @staticmethod
    def _conversation_key(project_id: str, participant_ids: list[str]) -> str:
        return f"{project_id}:{participant_ids[0]}:{participant_ids[1]}"

    @staticmethod
    def _encode_cursor(sort_time: datetime, item_id: str) -> str:
        api_time = api_datetime(sort_time)
        raw = f"{api_time.isoformat()}|{item_id}"
        return urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[datetime, str]:
        try:
            padding = "=" * (-len(cursor) % 4)
            raw = urlsafe_b64decode(cursor + padding).decode("utf-8")
            sort_time, item_id = raw.split("|", 1)
            parsed = datetime.fromisoformat(sort_time)
            if parsed.tzinfo is None or not item_id:
                raise ValueError
            return parsed.astimezone(UTC).replace(tzinfo=None), item_id
        except (ValueError, UnicodeDecodeError):
            raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422) from None

    @staticmethod
    def _require_conversation_participant(
        session: Session, conversation_id: str, requester_id: str
    ) -> None:
        participant = session.scalar(
            select(ConversationParticipantRow.user_id).where(
                ConversationParticipantRow.conversation_id == conversation_id,
                ConversationParticipantRow.user_id == requester_id,
                ConversationParticipantRow.status == "ACTIVE",
            )
        )
        if participant is None:
            raise ServiceError("RESOURCE_NOT_FOUND", "会话不存在或不可见。", 404)

    @staticmethod
    def _active_member(session: Session, project_id: str, user_id: str) -> ProjectMemberRow | None:
        return session.scalar(
            select(ProjectMemberRow).where(
                ProjectMemberRow.project_id == project_id,
                ProjectMemberRow.user_id == user_id,
                ProjectMemberRow.status == "ACTIVE",
            )
        )

    @staticmethod
    def _require_open_role_capacity(session: Session, role: ProjectRoleRow) -> None:
        if role.status != "OPEN":
            raise ServiceError("ROLE_NOT_OPEN", "岗位当前不接受新成员。", 409)
        filled_count = session.scalar(
            select(func.count(ProjectMemberRow.id)).where(
                ProjectMemberRow.role_id == role.id,
                ProjectMemberRow.status == "ACTIVE",
            )
        )
        if (filled_count or 0) >= role.headcount:
            raise ServiceError("ROLE_FULL", "岗位容量已满。", 409)

    @staticmethod
    def _invitation_pending_key(project_id: str, role_id: str, invitee_id: str) -> str:
        return f"{project_id}:{role_id}:{invitee_id}"

    @staticmethod
    def _match_preferences_query() -> Select[tuple[MatchPreferenceRow]]:
        return select(MatchPreferenceRow).options(
            selectinload(MatchPreferenceRow.directions),
            selectinload(MatchPreferenceRow.availability_slots),
        )

    @staticmethod
    def _project_query() -> Select[tuple[ProjectRow]]:
        return select(ProjectRow).options(
            selectinload(ProjectRow.roles).selectinload(ProjectRoleRow.skills),
            selectinload(ProjectRow.roles).selectinload(ProjectRoleRow.availability_slots),
            selectinload(ProjectRow.scenarios),
            selectinload(ProjectRow.members),
        )

    @staticmethod
    def _apply_profile(row: ProfileRow, payload: ProfilePayload) -> None:
        row.nickname = payload.nickname
        row.school = payload.school
        row.major = payload.major
        row.grade = payload.grade
        row.role_preference = payload.rolePreference
        row.hours_per_week = payload.hoursPerWeek
        row.bio = payload.bio
        row.visibility = payload.visibility
        row.skills = [ProfileSkillRow(position=index, skill_name=value) for index, value in enumerate(payload.skills)]
        row.scenarios = [
            ProfileScenarioRow(position=index, scenario_name=value)
            for index, value in enumerate(payload.collaborationScenarios)
        ]

    @staticmethod
    def _apply_match_preferences(row: MatchPreferenceRow, payload: MatchPreferencesPayload) -> None:
        row.directions = [
            MatchPreferenceDirectionRow(position=index, direction_code=value)
            for index, value in enumerate(payload.desiredDirections)
        ]
        row.availability_slots = [
            MatchPreferenceAvailabilitySlotRow(
                position=index,
                timezone=slot.timezone,
                weekday=slot.weekday,
                start_minute=slot.startMinute,
                end_minute=slot.endMinute,
            )
            for index, slot in enumerate(payload.availabilitySlots)
        ]

    @staticmethod
    def _replace_roles(
        row: ProjectRow,
        payload_roles: list,
        existing_roles: list[RoleData] | None = None,
    ) -> None:
        existing_roles = existing_roles or []
        role_rows: list[ProjectRoleRow] = []
        for index, role in enumerate(payload_roles):
            existing = existing_roles[index] if index < len(existing_roles) else None
            required_keys = {
                value.strip().casefold()
                for value in (
                    role.requiredSkills
                    if role.requiredSkills is not None
                    else existing.requiredSkills if existing else []
                )
            }
            slot_payloads = (
                role.requiredAvailabilitySlots
                if role.requiredAvailabilitySlots is not None
                else existing.requiredAvailabilitySlots if existing else []
            )
            role_rows.append(
                ProjectRoleRow(
                    id=existing.id if existing else f"role_{uuid4().hex}",
                    position=index,
                    name=role.name,
                    headcount=role.headcount,
                    hours_per_week=role.hoursPerWeek,
                    description=role.description,
                    status=role.status,
                    collaboration_role=(
                        role.collaborationRole
                        if role.collaborationRole is not None
                        else existing.collaborationRole if existing else "MEMBER"
                    ),
                    skills=[
                        ProjectRoleSkillRow(
                            position=skill_index,
                            skill_name=skill,
                            required=skill.strip().casefold() in required_keys,
                        )
                        for skill_index, skill in enumerate(role.skills)
                    ],
                    availability_slots=[
                        ProjectRoleAvailabilitySlotRow(
                            position=slot_index,
                            timezone=slot.timezone,
                            weekday=slot.weekday,
                            start_minute=slot.startMinute,
                            end_minute=slot.endMinute,
                        )
                        for slot_index, slot in enumerate(slot_payloads)
                    ],
                )
            )
        row.roles = role_rows

    @staticmethod
    def _replace_project_scenarios(row: ProjectRow, scenarios: list[str]) -> None:
        row.scenarios = [
            ProjectScenarioRow(position=index, scenario_code=value)
            for index, value in enumerate(scenarios)
        ]

    @staticmethod
    def _profile_data(row: ProfileRow) -> ProfileData:
        return ProfileData.model_validate(
            {
                "nickname": row.nickname,
                "school": row.school,
                "major": row.major,
                "grade": row.grade,
                "skills": [item.skill_name for item in sorted(row.skills, key=lambda item: item.position)],
                "collaborationScenarios": [
                    item.scenario_name for item in sorted(row.scenarios, key=lambda item: item.position)
                ],
                "rolePreference": row.role_preference,
                "hoursPerWeek": row.hours_per_week,
                "bio": row.bio,
                "visibility": row.visibility,
                "version": row.version,
                "updatedAt": api_datetime(row.updated_at),
            }
        )

    @staticmethod
    def _public_profile_data(user_id: str, row: ProfileRow) -> PublicProfileData:
        data = SqlAlchemyStore._profile_data(row).model_dump()
        data.pop("version", None)
        return PublicProfileData.model_validate({"id": user_id, **data})

    @staticmethod
    def _match_preferences_data(row: MatchPreferenceRow) -> MatchPreferencesData:
        return MatchPreferencesData.model_validate(
            {
                "desiredDirections": [
                    item.direction_code for item in sorted(row.directions, key=lambda item: item.position)
                ],
                "availabilitySlots": [
                    {
                        "timezone": item.timezone,
                        "weekday": item.weekday,
                        "startMinute": item.start_minute,
                        "endMinute": item.end_minute,
                    }
                    for item in sorted(row.availability_slots, key=lambda item: item.position)
                ],
                "version": row.version,
                "updatedAt": api_datetime(row.updated_at),
            }
        )

    @staticmethod
    def _project_data(row: ProjectRow) -> ProjectData:
        roles = sorted(row.roles, key=lambda item: item.position)
        filled_by_role: dict[str, int] = {}
        for member in row.members:
            if member.status == "ACTIVE":
                filled_by_role[member.role_id] = filled_by_role.get(member.role_id, 0) + 1
        return ProjectData.model_validate(
            {
                "id": row.id,
                "ownerId": row.owner_id,
                "title": row.title,
                "description": row.description,
                "direction": row.direction,
                "competition": row.competition,
                "stage": row.stage,
                "teamInfo": row.team_info,
                "collaborationScenarios": [
                    item.scenario_code for item in sorted(row.scenarios, key=lambda item: item.position)
                ],
                "status": row.status,
                "version": row.version,
                "publishedAt": api_datetime(row.published_at),
                "createdAt": api_datetime(row.created_at),
                "updatedAt": api_datetime(row.updated_at),
                "roles": [
                    RoleData.model_validate(
                        {
                            "id": role.id,
                            "name": role.name,
                            "skills": [
                                item.skill_name for item in sorted(role.skills, key=lambda item: item.position)
                            ],
                            "requiredSkills": [
                                item.skill_name
                                for item in sorted(role.skills, key=lambda item: item.position)
                                if item.required
                            ],
                            "requiredAvailabilitySlots": [
                                {
                                    "timezone": item.timezone,
                                    "weekday": item.weekday,
                                    "startMinute": item.start_minute,
                                    "endMinute": item.end_minute,
                                }
                                for item in sorted(role.availability_slots, key=lambda item: item.position)
                            ],
                            "collaborationRole": role.collaboration_role,
                            "filledCount": filled_by_role.get(role.id, 0),
                            "remainingCount": role.headcount - filled_by_role.get(role.id, 0),
                            "headcount": role.headcount,
                            "hoursPerWeek": role.hours_per_week,
                            "description": role.description,
                            "status": role.status,
                        }
                    )
                    for role in roles
                ],
            }
        )

    @staticmethod
    def _project_member_data(row: ProjectMemberRow, role_name: str) -> ProjectMemberData:
        return ProjectMemberData.model_validate(
            {
                "id": row.id,
                "projectId": row.project_id,
                "roleId": row.role_id,
                "roleName": role_name,
                "userId": row.user_id,
                "status": row.status,
                "joinedAt": api_datetime(row.joined_at),
            }
        )

    @staticmethod
    def _invitation_data(row: InvitationRow) -> InvitationData:
        return InvitationData.model_validate(
            {
                "id": row.id,
                "projectId": row.project_id,
                "roleId": row.role_id,
                "inviterUserId": row.inviter_id,
                "inviteeUserId": row.invitee_id,
                "status": row.status,
                "expiresAt": api_datetime(row.expires_at),
                "createdAt": api_datetime(row.created_at),
                "respondedAt": api_datetime(row.responded_at),
            }
        )

    @staticmethod
    def _conversation_data(session: Session, row: ConversationRow) -> ConversationData:
        participant_ids = list(
            session.scalars(
                select(ConversationParticipantRow.user_id)
                .where(
                    ConversationParticipantRow.conversation_id == row.id,
                    ConversationParticipantRow.status == "ACTIVE",
                )
                .order_by(ConversationParticipantRow.user_id)
            )
        )
        return ConversationData.model_validate(
            {
                "id": row.id,
                "projectId": row.project_id,
                "participantUserIds": participant_ids,
                "lastMessageAt": api_datetime(row.last_message_at),
                "createdAt": api_datetime(row.created_at),
            }
        )

    @staticmethod
    def _message_data(row: MessageRow) -> MessageData:
        return MessageData.model_validate(
            {
                "id": row.id,
                "conversationId": row.conversation_id,
                "senderUserId": row.sender_id,
                "clientMessageId": row.client_message_id,
                "type": row.type,
                "content": row.content,
                "status": row.status,
                "createdAt": api_datetime(row.created_at),
            }
        )

    @staticmethod
    def _require_owner(row: ProjectRow | None, user_id: str) -> None:
        if row is None:
            raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
        if row.owner_id != user_id:
            raise ServiceError("FORBIDDEN", "你没有权限操作该项目。", 403)
