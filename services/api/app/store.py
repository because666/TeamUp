from base64 import urlsafe_b64decode, urlsafe_b64encode
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import RLock
from typing import Protocol
from uuid import uuid4

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
    ProfilePayload,
    ProjectData,
    ProjectMemberData,
    ProjectPayload,
    ProjectUpdate,
    RoleData,
    RolePayload,
    MatchResultData,
    RecommendationImpressionData,
    RecommendationImpressionRequest,
    ReportData,
    ReportRequest,
)
from .matching_service import (
    MatchSnapshot,
    build_profile_match,
    build_project_match,
    page_snapshot,
    validate_impression_time,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


class Store(Protocol):
    def login(self, subject: str) -> tuple[str, str, bool]: ...
    def user_for_token(self, token: str) -> str: ...
    def logout(self, token: str, request_id: str = "req_unknown") -> None: ...
    def request_account_deletion(self, user_id: str, request_id: str) -> AccountDeletionRequestData: ...
    def create_block(self, blocker_id: str, blocked_id: str) -> BlockData: ...
    def remove_block(self, blocker_id: str, blocked_id: str) -> bool: ...
    def users_blocked(self, first_user_id: str, second_user_id: str) -> bool: ...
    def create_invitation(
        self, inviter_id: str, project_id: str, role_id: str, invitee_id: str
    ) -> InvitationData: ...
    def accept_invitation(self, invitee_id: str, invitation_id: str) -> InvitationAcceptData: ...
    def reject_invitation(self, invitee_id: str, invitation_id: str) -> InvitationData: ...
    def create_conversation(
        self, requester_id: str, project_id: str, other_user_id: str
    ) -> ConversationData: ...
    def list_conversations(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[ConversationData], str | None]: ...
    def list_messages(
        self, requester_id: str, conversation_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MessageData], str | None]: ...
    def send_message(
        self, requester_id: str, conversation_id: str, client_message_id: str, content: str
    ) -> MessageData: ...
    def get_profile(self, user_id: str) -> ProfileData | None: ...
    def get_public_profile(self, requester_id: str, user_id: str) -> PublicProfileData: ...
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
    ) -> tuple[list[PublicProfileData], str | None]: ...
    def save_profile(self, user_id: str, payload: ProfilePayload, version: int | None) -> ProfileData: ...
    def get_match_preferences(self, user_id: str) -> MatchPreferencesData | None: ...
    def save_match_preferences(
        self, user_id: str, payload: MatchPreferencesPayload, version: int | None
    ) -> MatchPreferencesData: ...
    def create_project(self, user_id: str, payload: ProjectPayload) -> ProjectData: ...
    def get_project(self, project_id: str, requester_id: str | None = None) -> ProjectData: ...
    def update_project(self, user_id: str, project_id: str, payload: ProjectUpdate) -> ProjectData: ...
    def publish_project(self, user_id: str, project_id: str, version: int) -> ProjectData: ...
    def close_project(self, user_id: str, project_id: str, version: int) -> ProjectData: ...
    def add_project_member(self, project_id: str, role_id: str, user_id: str) -> ProjectMemberData: ...
    def list_project_members(self, requester_id: str, project_id: str) -> list[ProjectMemberData]: ...
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
    ) -> tuple[list[ProjectData], str | None]: ...
    def list_my_projects(
        self, user_id: str, status: str | None, limit: int, cursor: str | None
    ) -> tuple[list[ProjectData], str | None]: ...
    def project_matches(
        self, requester_id: str, project_id: str, role_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]: ...
    def user_project_matches(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]: ...
    def record_recommendation_impressions(
        self, requester_id: str, payload: RecommendationImpressionRequest
    ) -> list[RecommendationImpressionData]: ...
    def create_report(self, reporter_id: str, payload: ReportRequest, request_id: str) -> ReportData: ...
    def ready(self) -> bool: ...


class MemoryStore:
    """Local/test persistence adapter; production must replace this with MySQL."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.users_by_subject: dict[str, str] = {}
        self.sessions: dict[str, tuple[str, datetime]] = {}
        self.user_statuses: dict[str, str] = {}
        self.account_deletion_requests: dict[str, AccountDeletionRequestData] = {}
        self.pending_deletion_by_user: dict[str, str] = {}
        self.audit_events: list[dict[str, object]] = []
        self.blocks: dict[tuple[str, str], BlockData] = {}
        self.invitations: dict[str, InvitationData] = {}
        self.conversations: dict[str, ConversationData] = {}
        self.messages: dict[str, MessageData] = {}
        self.profiles: dict[str, ProfileData] = {}
        self.match_preferences: dict[str, MatchPreferencesData] = {}
        self.projects: dict[str, ProjectData] = {}
        self.project_members: dict[str, ProjectMemberData] = {}
        self.match_snapshots: dict[str, MatchSnapshot] = {}
        self.recommendation_impressions: dict[tuple[str, str, str, str], RecommendationImpressionData] = {}
        self.reports: dict[str, ReportData] = {}
        self.report_reporters: dict[str, str] = {}
        self.report_descriptions: dict[str, str] = {}

    def ready(self) -> bool:
        return True

    def login(self, subject: str) -> tuple[str, str, bool]:
        with self._lock:
            user_id = self.users_by_subject.setdefault(subject, f"usr_{uuid4().hex}")
            if self.user_statuses.setdefault(user_id, "ACTIVE") != "ACTIVE":
                raise ServiceError("FORBIDDEN", "当前账号状态不允许登录。", 403)
            token = f"tu_{token_urlsafe(32)}"
            self.sessions[token] = (user_id, now_utc() + timedelta(hours=12))
            return user_id, token, user_id in self.profiles

    def user_for_token(self, token: str) -> str:
        with self._lock:
            session = self.sessions.get(token)
            if (
                not session
                or session[1] <= now_utc()
                or self.user_statuses.get(session[0], "ACTIVE") != "ACTIVE"
            ):
                self.sessions.pop(token, None)
                raise ServiceError("SESSION_EXPIRED", "登录状态已失效，请重新登录。", 401)
            return session[0]

    def logout(self, token: str, request_id: str = "req_unknown") -> None:
        with self._lock:
            session = self.sessions.pop(token, None)
            if session is not None:
                self._append_audit_event(
                    session[0], "LOGOUT", "SESSION", "CURRENT_SESSION", request_id
                )

    def request_account_deletion(self, user_id: str, request_id: str) -> AccountDeletionRequestData:
        with self._lock:
            existing_id = self.pending_deletion_by_user.get(user_id)
            if existing_id is not None:
                return deepcopy(self.account_deletion_requests[existing_id])
            if self.user_statuses.get(user_id, "ACTIVE") != "ACTIVE":
                raise ServiceError("ACCOUNT_NOT_ACTIVE", "当前账号状态不允许申请注销。", 409)
            request_data = AccountDeletionRequestData(
                id=f"adrq_{uuid4().hex}",
                status="PENDING",
                requestedAt=now_utc(),
            )
            self.account_deletion_requests[request_data.id] = request_data
            self.pending_deletion_by_user[user_id] = request_data.id
            self.user_statuses[user_id] = "DELETION_PENDING"
            self.sessions = {
                token: session for token, session in self.sessions.items() if session[0] != user_id
            }
            self._append_audit_event(
                user_id, "ACCOUNT_DELETION_REQUESTED", "ACCOUNT_DELETION_REQUEST",
                request_data.id, request_id
            )
            return deepcopy(request_data)

    def create_block(self, blocker_id: str, blocked_id: str) -> BlockData:
        with self._lock:
            if blocker_id == blocked_id:
                raise ServiceError("CANNOT_BLOCK_SELF", "不能拉黑自己。", 422)
            if blocked_id not in self.users_by_subject.values():
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可见。", 404)
            key = (blocker_id, blocked_id)
            existing = self.blocks.get(key)
            if existing is not None:
                return deepcopy(existing)
            block = BlockData(blockedUserId=blocked_id, createdAt=now_utc())
            self.blocks[key] = block
            return deepcopy(block)

    def remove_block(self, blocker_id: str, blocked_id: str) -> bool:
        with self._lock:
            return self.blocks.pop((blocker_id, blocked_id), None) is not None

    def users_blocked(self, first_user_id: str, second_user_id: str) -> bool:
        with self._lock:
            return (first_user_id, second_user_id) in self.blocks or (
                second_user_id,
                first_user_id,
            ) in self.blocks

    def create_invitation(
        self, inviter_id: str, project_id: str, role_id: str, invitee_id: str
    ) -> InvitationData:
        with self._lock:
            project = self.projects.get(project_id)
            self._require_owner(project, inviter_id)
            if inviter_id == invitee_id:
                raise ServiceError("CANNOT_INVITE_SELF", "不能邀请自己加入项目。", 422)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许创建邀请。", 409)
            if invitee_id not in self.users_by_subject.values():
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可见。", 404)
            if self.users_blocked(inviter_id, invitee_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许创建邀请。", 409)
            role = next((item for item in project.roles if item.id == role_id), None)
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if role.status != "OPEN":
                raise ServiceError("ROLE_NOT_OPEN", "岗位当前不接受邀请。", 409)
            if any(
                member.projectId == project_id and member.userId == invitee_id and member.status == "ACTIVE"
                for member in self.project_members.values()
            ):
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409)
            if role.filledCount >= role.headcount:
                raise ServiceError("ROLE_FULL", "岗位容量已满。", 409)

            timestamp = now_utc()
            for invitation_id, invitation in list(self.invitations.items()):
                if (
                    invitation.projectId == project_id
                    and invitation.roleId == role_id
                    and invitation.inviteeUserId == invitee_id
                    and invitation.status == "PENDING"
                ):
                    if invitation.expiresAt > timestamp:
                        return deepcopy(invitation)
                    self.invitations[invitation_id] = invitation.model_copy(
                        update={"status": "EXPIRED", "respondedAt": timestamp}
                    )

            invitation = InvitationData(
                id=f"inv_{uuid4().hex}",
                projectId=project_id,
                roleId=role_id,
                inviterUserId=inviter_id,
                inviteeUserId=invitee_id,
                status="PENDING",
                expiresAt=timestamp + timedelta(days=7),
                createdAt=timestamp,
            )
            self.invitations[invitation.id] = invitation
            return deepcopy(invitation)

    def accept_invitation(self, invitee_id: str, invitation_id: str) -> InvitationAcceptData:
        with self._lock:
            invitation = self._invitation_for_invitee(invitation_id, invitee_id)
            if invitation.status == "ACCEPTED":
                member = next(
                    (
                        item
                        for item in self.project_members.values()
                        if item.projectId == invitation.projectId and item.userId == invitee_id
                    ),
                    None,
                )
                if member is None:
                    raise ServiceError("INTERNAL_ERROR", "邀请成员状态不一致。", 500)
                return InvitationAcceptData(invitation=deepcopy(invitation), member=deepcopy(member))
            if invitation.status != "PENDING" or invitation.expiresAt <= now_utc():
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可接受。", 409)
            member = self.add_project_member(invitation.projectId, invitation.roleId, invitee_id)
            accepted = invitation.model_copy(update={"status": "ACCEPTED", "respondedAt": now_utc()})
            self.invitations[invitation_id] = accepted
            return InvitationAcceptData(invitation=deepcopy(accepted), member=member)

    def reject_invitation(self, invitee_id: str, invitation_id: str) -> InvitationData:
        with self._lock:
            invitation = self._invitation_for_invitee(invitation_id, invitee_id)
            if invitation.status == "REJECTED":
                return deepcopy(invitation)
            if invitation.status != "PENDING" or invitation.expiresAt <= now_utc():
                raise ServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理、过期或不可拒绝。", 409)
            rejected = invitation.model_copy(update={"status": "REJECTED", "respondedAt": now_utc()})
            self.invitations[invitation_id] = rejected
            return deepcopy(rejected)

    def create_conversation(
        self, requester_id: str, project_id: str, other_user_id: str
    ) -> ConversationData:
        with self._lock:
            if requester_id == other_user_id:
                raise ServiceError("CANNOT_MESSAGE_SELF", "不能与自己创建会话。", 422)
            project = self.projects.get(project_id)
            if project is None or project.status != "PUBLISHED":
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可联系。", 404)
            if other_user_id not in self.users_by_subject.values():
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在或不可联系。", 404)
            active_member_ids = {
                member.userId
                for member in self.project_members.values()
                if member.projectId == project_id and member.status == "ACTIVE"
            }
            if not ({requester_id, other_user_id} & ({project.ownerId} | active_member_ids)):
                raise ServiceError("FORBIDDEN", "当前用户关系不能基于该项目创建会话。", 403)
            if self.users_blocked(requester_id, other_user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许创建会话。", 409)
            participants = sorted((requester_id, other_user_id))
            existing = next(
                (
                    item
                    for item in self.conversations.values()
                    if item.projectId == project_id and item.participantUserIds == participants
                ),
                None,
            )
            if existing is not None:
                return deepcopy(existing)
            timestamp = now_utc()
            conversation = ConversationData(
                id=f"con_{uuid4().hex}",
                projectId=project_id,
                participantUserIds=participants,
                lastMessageAt=None,
                createdAt=timestamp,
            )
            self.conversations[conversation.id] = conversation
            return deepcopy(conversation)

    def list_conversations(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[ConversationData], str | None]:
        with self._lock:
            conversations = sorted(
                (item for item in self.conversations.values() if requester_id in item.participantUserIds),
                key=lambda item: (item.lastMessageAt or item.createdAt, item.id),
                reverse=True,
            )
            if cursor:
                cursor_time, cursor_id = self._decode_cursor(cursor)
                conversations = [
                    item
                    for item in conversations
                    if (item.lastMessageAt or item.createdAt, item.id) < (cursor_time, cursor_id)
                ]
            page = conversations[:limit]
            has_more = len(conversations) > limit
            return deepcopy(page), (
                self._encode_cursor(page[-1].lastMessageAt or page[-1].createdAt, page[-1].id)
                if has_more and page
                else None
            )

    def list_messages(
        self, requester_id: str, conversation_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MessageData], str | None]:
        with self._lock:
            self._require_conversation_participant(conversation_id, requester_id)
            messages = sorted(
                (item for item in self.messages.values() if item.conversationId == conversation_id),
                key=lambda item: (item.createdAt, item.id),
            )
            if cursor:
                cursor_time, cursor_id = self._decode_cursor(cursor)
                messages = [
                    item for item in messages if (item.createdAt, item.id) > (cursor_time, cursor_id)
                ]
            page = messages[:limit]
            has_more = len(messages) > limit
            return deepcopy(page), (
                self._encode_cursor(page[-1].createdAt, page[-1].id) if has_more and page else None
            )

    def send_message(
        self, requester_id: str, conversation_id: str, client_message_id: str, content: str
    ) -> MessageData:
        with self._lock:
            conversation = self._require_conversation_participant(conversation_id, requester_id)
            other_user_id = next(item for item in conversation.participantUserIds if item != requester_id)
            existing = next(
                (
                    item
                    for item in self.messages.values()
                    if item.senderUserId == requester_id and item.clientMessageId == client_message_id
                ),
                None,
            )
            if existing is not None:
                if existing.conversationId != conversation_id or existing.content != content:
                    raise ServiceError(
                        "MESSAGE_IDEMPOTENCY_CONFLICT", "消息幂等键已用于不同内容。", 409
                    )
                return deepcopy(existing)
            if self.users_blocked(requester_id, other_user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许发送消息。", 409)
            timestamp = now_utc()
            message = MessageData(
                id=f"msg_{uuid4().hex}",
                conversationId=conversation_id,
                senderUserId=requester_id,
                clientMessageId=client_message_id,
                content=content,
                createdAt=timestamp,
            )
            self.messages[message.id] = message
            self.conversations[conversation_id] = conversation.model_copy(update={"lastMessageAt": timestamp})
            return deepcopy(message)

    def get_profile(self, user_id: str) -> ProfileData | None:
        with self._lock:
            return deepcopy(self.profiles.get(user_id))

    def get_public_profile(self, requester_id: str, user_id: str) -> PublicProfileData:
        with self._lock:
            if requester_id == user_id:
                raise ServiceError("RESOURCE_NOT_FOUND", "公开名片不存在或不可见。", 404)
            profile = self.profiles.get(user_id)
            if (
                profile is None
                or self.user_statuses.get(user_id) != "ACTIVE"
                or not profile.visibility
                or self.users_blocked(requester_id, user_id)
            ):
                raise ServiceError("RESOURCE_NOT_FOUND", "公开名片不存在或不可见。", 404)
            return self._public_profile_data(user_id, profile)

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
        with self._lock:
            profiles = []
            for user_id, profile in self.profiles.items():
                if (
                    user_id == requester_id
                    or self.user_statuses.get(user_id) != "ACTIVE"
                    or not profile.visibility
                    or self.users_blocked(requester_id, user_id)
                ):
                    continue
                if skill and not any(value.casefold() == skill.casefold() for value in profile.skills):
                    continue
                preferences = self.match_preferences.get(user_id)
                if direction and (preferences is None or not any(value.casefold() == direction.casefold() for value in preferences.desiredDirections)):
                    continue
                if collaboration_role and profile.rolePreference != collaboration_role:
                    continue
                if min_hours_per_week is not None and profile.hoursPerWeek < min_hours_per_week:
                    continue
                if max_hours_per_week is not None and profile.hoursPerWeek > max_hours_per_week:
                    continue
                profiles.append(self._public_profile_data(user_id, profile))
            profiles.sort(key=lambda item: (item.updatedAt, item.id), reverse=True)
            start = self._cursor_start(profiles, cursor)
            page = profiles[start : start + limit]
            has_more = start + limit < len(profiles)
            return deepcopy(page), page[-1].id if has_more and page else None

    def save_profile(self, user_id: str, payload: ProfilePayload, version: int | None) -> ProfileData:
        with self._lock:
            existing = self.profiles.get(user_id)
            if existing and version != existing.version:
                raise ServiceError("VERSION_CONFLICT", "能力名片已被更新，请重新加载后再保存。", 409)
            if not existing and version not in (None, 0):
                raise ServiceError("VERSION_CONFLICT", "能力名片版本已失效，请重新加载。", 409)
            timestamp = now_utc()
            saved = ProfileData.model_validate(
                {
                    **payload.model_dump(),
                    "version": (existing.version + 1 if existing else 1),
                    "updatedAt": timestamp,
                }
            )
            self.profiles[user_id] = saved
            return deepcopy(saved)

    def get_match_preferences(self, user_id: str) -> MatchPreferencesData | None:
        with self._lock:
            return deepcopy(self.match_preferences.get(user_id))

    def save_match_preferences(
        self,
        user_id: str,
        payload: MatchPreferencesPayload,
        version: int | None,
    ) -> MatchPreferencesData:
        with self._lock:
            if user_id not in self.users_by_subject.values():
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            existing = self.match_preferences.get(user_id)
            if existing and version != existing.version:
                raise ServiceError("VERSION_CONFLICT", "匹配偏好已被更新，请重新加载后再保存。", 409)
            if not existing and version not in (None, 0):
                raise ServiceError("VERSION_CONFLICT", "匹配偏好版本已失效，请重新加载。", 409)
            saved = MatchPreferencesData.model_validate(
                {
                    **payload.model_dump(),
                    "version": existing.version + 1 if existing else 1,
                    "updatedAt": now_utc(),
                }
            )
            self.match_preferences[user_id] = saved
            return deepcopy(saved)

    def create_project(self, user_id: str, payload: ProjectPayload) -> ProjectData:
        with self._lock:
            timestamp = now_utc()
            project_id = f"prj_{uuid4().hex}"
            data = ProjectData.model_validate(
                {
                    **payload.model_dump(exclude={"roles", "collaborationScenarios"}),
                    "id": project_id,
                    "ownerId": user_id,
                    "status": "DRAFT",
                    "version": 1,
                    "publishedAt": None,
                    "createdAt": timestamp,
                    "updatedAt": timestamp,
                    "roles": [self._role_data(role, f"role_{uuid4().hex}") for role in payload.roles],
                    "collaborationScenarios": payload.collaborationScenarios or [],
                }
            )
            self.projects[project_id] = data
            return deepcopy(data)

    def get_project(self, project_id: str, requester_id: str | None = None) -> ProjectData:
        with self._lock:
            project = self.projects.get(project_id)
            if not project:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            if requester_id is not None and project.ownerId != requester_id:
                if (
                    project.status == "DRAFT"
                    or self.user_statuses.get(project.ownerId) != "ACTIVE"
                    or self.users_blocked(requester_id, project.ownerId)
                ):
                    raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            return deepcopy(project)

    def update_project(self, user_id: str, project_id: str, payload: ProjectUpdate) -> ProjectData:
        with self._lock:
            project = self.projects.get(project_id)
            self._require_owner(project, user_id)
            if project.status != "DRAFT":
                raise ServiceError("PROJECT_NOT_EDITABLE", "项目当前状态不可编辑。", 409)
            if payload.version != project.version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再保存。", 409)
            timestamp = now_utc()
            updated = ProjectData.model_validate(
                {
                    **payload.model_dump(exclude={"version", "roles", "collaborationScenarios"}),
                    "id": project.id,
                    "ownerId": project.ownerId,
                    "status": project.status,
                    "version": project.version + 1,
                    "publishedAt": project.publishedAt,
                    "createdAt": project.createdAt,
                    "updatedAt": timestamp,
                    "roles": [
                        self._role_data(
                            role,
                            project.roles[index].id if index < len(project.roles) else f"role_{uuid4().hex}",
                            project.roles[index] if index < len(project.roles) else None,
                        )
                        for index, role in enumerate(payload.roles)
                    ],
                    "collaborationScenarios": (
                        payload.collaborationScenarios
                        if payload.collaborationScenarios is not None
                        else project.collaborationScenarios
                    ),
                }
            )
            self.projects[project_id] = updated
            return deepcopy(updated)

    def publish_project(self, user_id: str, project_id: str, version: int) -> ProjectData:
        with self._lock:
            project = self.projects.get(project_id)
            self._require_owner(project, user_id)
            if project.status != "DRAFT":
                raise ServiceError("PROJECT_NOT_PUBLISHABLE", "项目当前状态不可发布。", 409)
            if version != project.version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再发布。", 409)
            if not any(role.status == "OPEN" for role in project.roles):
                raise ServiceError("PROJECT_NOT_PUBLISHABLE", "至少需要一个开放岗位才能发布。", 409)
            timestamp = now_utc()
            published = project.model_copy(
                update={
                    "status": "PUBLISHED",
                    "version": project.version + 1,
                    "publishedAt": timestamp,
                    "updatedAt": timestamp,
                }
            )
            self.projects[project_id] = published
            return deepcopy(published)

    def close_project(self, user_id: str, project_id: str, version: int) -> ProjectData:
        with self._lock:
            project = self.projects.get(project_id)
            self._require_owner(project, user_id)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_CLOSABLE", "只有已发布项目可以关闭。", 409)
            if version != project.version:
                raise ServiceError("VERSION_CONFLICT", "项目已被更新，请重新加载后再关闭。", 409)
            closed = project.model_copy(update={"status": "CLOSED", "version": project.version + 1, "updatedAt": now_utc()})
            self.projects[project_id] = closed
            return deepcopy(closed)

    def add_project_member(self, project_id: str, role_id: str, user_id: str) -> ProjectMemberData:
        with self._lock:
            project = self.projects.get(project_id)
            if not project:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许新增成员。", 409)
            if user_id not in self.users_by_subject.values():
                raise ServiceError("RESOURCE_NOT_FOUND", "用户不存在。", 404)
            if self.users_blocked(project.ownerId, user_id):
                raise ServiceError("USER_BLOCKED", "当前用户关系不允许新增成员。", 409)
            role = next((item for item in project.roles if item.id == role_id), None)
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if role.status != "OPEN":
                raise ServiceError("ROLE_NOT_OPEN", "岗位当前不接受新成员。", 409)
            if any(
                member.projectId == project_id and member.userId == user_id and member.status == "ACTIVE"
                for member in self.project_members.values()
            ):
                raise ServiceError("MEMBER_ALREADY_EXISTS", "用户已经是该项目成员。", 409)
            if role.filledCount >= role.headcount:
                raise ServiceError("ROLE_FULL", "岗位容量已满。", 409)

            member = ProjectMemberData(
                id=f"mem_{uuid4().hex}",
                projectId=project_id,
                roleId=role_id,
                roleName=role.name,
                userId=user_id,
                status="ACTIVE",
                joinedAt=now_utc(),
            )
            self.project_members[member.id] = member
            updated_roles = [
                item.model_copy(
                    update={
                        "filledCount": item.filledCount + 1,
                        "remainingCount": item.remainingCount - 1,
                    }
                )
                if item.id == role_id
                else item
                for item in project.roles
            ]
            self.projects[project_id] = project.model_copy(update={"roles": updated_roles})
            return deepcopy(member)

    def list_project_members(self, requester_id: str, project_id: str) -> list[ProjectMemberData]:
        with self._lock:
            project = self.projects.get(project_id)
            if not project:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
            members = [
                member
                for member in self.project_members.values()
                if member.projectId == project_id and member.status == "ACTIVE"
            ]
            if project.ownerId != requester_id and not any(member.userId == requester_id for member in members):
                raise ServiceError("FORBIDDEN", "你没有权限查看该项目成员。", 403)
            return deepcopy(sorted(members, key=lambda item: (item.joinedAt, item.id)))

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
        with self._lock:
            projects = sorted(
                (
                    project for project in self.projects.values()
                    if project.status == status
                    and self.user_statuses.get(project.ownerId) == "ACTIVE"
                    and (requester_id is None or not self.users_blocked(requester_id, project.ownerId))
                    and (direction is None or project.direction.casefold() == direction.casefold())
                    and (competition is None or project.competition.casefold() == competition.casefold())
                    and (stage is None or project.stage.casefold() == stage.casefold())
                    and (skill is None or any(skill.casefold() == value.casefold() for role in project.roles for value in role.skills))
                ),
                key=lambda item: (item.publishedAt or item.createdAt, item.id),
                reverse=True,
            )
            start = 0
            if cursor:
                ids = [project.id for project in projects]
                if cursor not in ids:
                    raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422)
                start = ids.index(cursor) + 1
            page = projects[start : start + limit]
            has_more = start + limit < len(projects)
            return deepcopy(page), (page[-1].id if has_more and page else None)

    def list_my_projects(
        self, user_id: str, status: str | None, limit: int, cursor: str | None
    ) -> tuple[list[ProjectData], str | None]:
        with self._lock:
            projects = [
                item for item in self.projects.values()
                if item.ownerId == user_id and (status is None or item.status == status)
            ]
            projects.sort(key=lambda item: (item.updatedAt, item.id), reverse=True)
            start = self._cursor_start(projects, cursor)
            page = projects[start : start + limit]
            has_more = start + limit < len(projects)
            return deepcopy(page), page[-1].id if has_more and page else None

    def project_matches(
        self, requester_id: str, project_id: str, role_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]:
        with self._lock:
            project = self.projects.get(project_id)
            self._require_owner(project, requester_id)
            if project.status != "PUBLISHED":
                raise ServiceError("PROJECT_NOT_MATCHABLE", "项目当前状态不允许匹配。", 409)
            role = next((item for item in project.roles if item.id == role_id), None)
            if role is None:
                raise ServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在。", 404)
            if role.status != "OPEN" or role.remainingCount <= 0:
                raise ServiceError("PROJECT_NOT_MATCHABLE", "岗位当前不允许匹配。", 409)
            results = []
            for candidate_id, profile in self.profiles.items():
                if (
                    candidate_id == requester_id
                    or self.user_statuses.get(candidate_id) != "ACTIVE"
                    or not profile.visibility
                    or self.users_blocked(requester_id, candidate_id)
                ):
                    continue
                if any(member.projectId == project_id and member.userId == candidate_id for member in self.project_members.values()):
                    continue
                preferences = self.match_preferences.get(candidate_id)
                result = build_profile_match(project, role, candidate_id, profile, preferences)
                if result is not None:
                    results.append(result)
            results.sort(key=lambda item: (-item.score, item.targetId))
            context = f"project:{requester_id}:{project_id}:{role_id}"
            return page_snapshot(
                self.match_snapshots, context, results, limit, cursor, viewer_user_id=requester_id
            )

    def user_project_matches(
        self, requester_id: str, limit: int, cursor: str | None
    ) -> tuple[list[MatchResultData], str | None, str]:
        with self._lock:
            profile = self.profiles.get(requester_id)
            if profile is None:
                raise ServiceError("MATCH_PROFILE_INCOMPLETE", "请先完成能力名片后再匹配。", 409)
            preferences = self.match_preferences.get(requester_id)
            if preferences is None:
                raise ServiceError("MATCH_PROFILE_INCOMPLETE", "请先完善匹配偏好后再匹配。", 409)
            results = []
            for project in self.projects.values():
                if (
                    project.status != "PUBLISHED"
                    or self.user_statuses.get(project.ownerId) != "ACTIVE"
                    or self.users_blocked(requester_id, project.ownerId)
                ):
                    continue
                if any(member.projectId == project.id and member.userId == requester_id for member in self.project_members.values()):
                    continue
                for role in project.roles:
                    result = build_project_match(requester_id, profile, preferences, project, role)
                    if result is not None:
                        results.append(result)
            results.sort(key=lambda item: (-item.score, item.targetId))
            context = f"user:{requester_id}"
            return page_snapshot(
                self.match_snapshots, context, results, limit, cursor, viewer_user_id=requester_id
            )

    def record_recommendation_impressions(
        self, requester_id: str, payload: RecommendationImpressionRequest
    ) -> list[RecommendationImpressionData]:
        with self._lock:
            snapshot = self.match_snapshots.get(payload.recommendationRequestId)
            if snapshot is None or snapshot.viewer_user_id != requester_id:
                raise ServiceError("RECOMMENDATION_REQUEST_INVALID", "推荐请求不存在或不可见。", 422)
            now = now_utc()
            if snapshot.expires_at <= now:
                self.match_snapshots.pop(payload.recommendationRequestId, None)
                raise ServiceError("RECOMMENDATION_EXPIRED", "推荐请求已过期，请重新加载。", 410)
            occurred_at = validate_impression_time(payload.occurredAt, now)
            candidates = {
                (result.targetType, result.targetId): result for result in snapshot.results
            }
            for item in payload.items:
                if (item.targetType, item.targetId) not in candidates:
                    raise ServiceError("INVALID_RECOMMENDATION_TARGET", "曝光候选不属于该推荐请求。", 422)
                if not self._impression_target_is_currently_valid(
                    requester_id, snapshot.context, item.targetType, item.targetId
                ):
                    raise ServiceError("INVALID_RECOMMENDATION_TARGET", "曝光候选当前已不可见。", 422)
                key = (payload.recommendationRequestId, requester_id, item.targetType, item.targetId)
                existing = self.recommendation_impressions.get(key)
                if existing is not None and existing.position != item.position:
                    raise ServiceError("IMPRESSION_CONFLICT", "同一候选的曝光位置不能变更。", 409)
            recorded: list[RecommendationImpressionData] = []
            for item in payload.items:
                key = (payload.recommendationRequestId, requester_id, item.targetType, item.targetId)
                existing = self.recommendation_impressions.get(key)
                if existing is not None:
                    recorded.append(existing.model_copy(update={"duplicate": True}))
                    continue
                impression = RecommendationImpressionData(
                    recommendationRequestId=payload.recommendationRequestId,
                    targetType=item.targetType,
                    targetId=item.targetId,
                    position=item.position,
                    recordedAt=now,
                    duplicate=False,
                )
                self.recommendation_impressions[key] = impression
                recorded.append(impression)
            return [item.model_copy(deep=True) for item in recorded]

    def _impression_target_is_currently_valid(
        self, requester_id: str, context: str, target_type: str, target_id: str
    ) -> bool:
        parts = context.split(":")
        if parts[0] == "project" and len(parts) == 4 and target_type == "PROFILE":
            _, owner_id, project_id, role_id = parts
            project = self.projects.get(project_id)
            role = next((item for item in project.roles if item.id == role_id), None) if project else None
            profile = self.profiles.get(target_id)
            return bool(
                owner_id == requester_id
                and project is not None
                and project.status == "PUBLISHED"
                and role is not None
                and role.status == "OPEN"
                and role.remainingCount > 0
                and profile is not None
                and self.user_statuses.get(target_id) == "ACTIVE"
                and profile.visibility
                and target_id != requester_id
                and not self.users_blocked(requester_id, target_id)
                and not any(
                    member.projectId == project_id
                    and member.userId == target_id
                    and member.status == "ACTIVE"
                    for member in self.project_members.values()
                )
            )
        if parts[0] == "user" and len(parts) == 2 and target_type == "PROJECT_ROLE":
            project_role_id = target_id
            for project in self.projects.values():
                role = next((item for item in project.roles if item.id == project_role_id), None)
                if role is None:
                    continue
                return bool(
                    project.status == "PUBLISHED"
                    and self.user_statuses.get(project.ownerId) == "ACTIVE"
                    and role.status == "OPEN"
                    and role.remainingCount > 0
                    and project.ownerId != requester_id
                    and not self.users_blocked(requester_id, project.ownerId)
                    and not any(
                        member.projectId == project.id
                        and member.userId == requester_id
                        and member.status == "ACTIVE"
                        for member in self.project_members.values()
                    )
                )
        return False

    def create_report(self, reporter_id: str, payload: ReportRequest, request_id: str) -> ReportData:
        with self._lock:
            for report in self.reports.values():
                if (
                    report.status == "PENDING"
                    and report.targetType == payload.targetType
                    and report.targetId == payload.targetId
                    and report.reason == payload.reason
                    and self.report_reporters.get(report.id) == reporter_id
                ):
                    return deepcopy(report)
            if not self._report_target_is_visible(reporter_id, payload.targetType, payload.targetId):
                raise ServiceError("RESOURCE_NOT_FOUND", "举报目标不存在或不可见。", 404)
            report = ReportData(
                id=f"rpt_{uuid4().hex}",
                targetType=payload.targetType,
                targetId=payload.targetId,
                reason=payload.reason,
                status="PENDING",
                createdAt=now_utc(),
            )
            self.reports[report.id] = report
            self.report_reporters[report.id] = reporter_id
            self.report_descriptions[report.id] = payload.description
            self._append_audit_event(
                reporter_id, "REPORT_SUBMITTED", "REPORT", report.id, request_id
            )
            return deepcopy(report)

    def _append_audit_event(
        self, actor_user_id: str, action: str, resource_type: str, resource_id: str, request_id: str
    ) -> None:
        self.audit_events.append(
            {
                "id": f"aud_{uuid4().hex}",
                "actorUserId": actor_user_id,
                "action": action,
                "resourceType": resource_type,
                "resourceId": resource_id,
                "requestId": request_id,
                "outcome": "SUCCESS",
                "createdAt": now_utc(),
            }
        )

    def _report_target_is_visible(self, reporter_id: str, target_type: str, target_id: str) -> bool:
        if target_type == "USER":
            return (
                target_id != reporter_id
                and target_id in self.users_by_subject.values()
                and self.user_statuses.get(target_id, "ACTIVE") == "ACTIVE"
            )
        if target_type == "PROJECT":
            project = self.projects.get(target_id)
            return bool(
                project is not None
                and project.status == "PUBLISHED"
                and project.ownerId != reporter_id
                and self.user_statuses.get(project.ownerId, "ACTIVE") == "ACTIVE"
            )
        if target_type == "MESSAGE":
            message = self.messages.get(target_id)
            conversation = self.conversations.get(message.conversationId) if message else None
            return bool(
                conversation is not None
                and reporter_id in conversation.participantUserIds
                and message.senderUserId != reporter_id
            )
        return False

    @staticmethod
    def _require_owner(project: ProjectData | None, user_id: str) -> None:
        if not project:
            raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
        if project.ownerId != user_id:
            raise ServiceError("FORBIDDEN", "你没有权限操作该项目。", 403)

    def _invitation_for_invitee(self, invitation_id: str, invitee_id: str) -> InvitationData:
        invitation = self.invitations.get(invitation_id)
        if invitation is None or invitation.inviteeUserId != invitee_id:
            raise ServiceError("RESOURCE_NOT_FOUND", "邀请不存在或不可见。", 404)
        return invitation

    def _require_conversation_participant(
        self, conversation_id: str, requester_id: str
    ) -> ConversationData:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or requester_id not in conversation.participantUserIds:
            raise ServiceError("RESOURCE_NOT_FOUND", "会话不存在或不可见。", 404)
        return conversation

    @staticmethod
    def _encode_cursor(sort_time: datetime, item_id: str) -> str:
        raw = f"{sort_time.isoformat()}|{item_id}"
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
            return parsed, item_id
        except (ValueError, UnicodeDecodeError):
            raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422) from None

    @staticmethod
    def _role_data(role: RolePayload, role_id: str, existing: RoleData | None = None) -> dict:
        skill_keys = {value.strip().casefold() for value in role.skills}
        if role.requiredSkills is None:
            existing_required_keys = (
                {value.strip().casefold() for value in existing.requiredSkills} if existing else set()
            )
            required_skills = [
                value for value in role.skills if value.strip().casefold() in existing_required_keys
            ]
        else:
            required_skills = role.requiredSkills
        required_slots = (
            role.requiredAvailabilitySlots
            if role.requiredAvailabilitySlots is not None
            else existing.requiredAvailabilitySlots if existing else []
        )
        collaboration_role = role.collaborationRole or (existing.collaborationRole if existing else "MEMBER")
        return {
            **role.model_dump(exclude={"requiredSkills", "requiredAvailabilitySlots", "collaborationRole"}),
            "id": role_id,
            "requiredSkills": required_skills,
            "requiredAvailabilitySlots": required_slots,
            "collaborationRole": collaboration_role,
            "filledCount": existing.filledCount if existing else 0,
            "remainingCount": role.headcount - (existing.filledCount if existing else 0),
        }

    @staticmethod
    def _public_profile_data(user_id: str, profile: ProfileData) -> PublicProfileData:
        return PublicProfileData.model_validate({"id": user_id, **profile.model_dump(exclude={"version"})})

    @staticmethod
    def _cursor_start(items: list[object], cursor: str | None) -> int:
        if not cursor:
            return 0
        item_id = cursor
        ids = [getattr(item, "id", None) for item in items]
        if item_id not in ids:
            raise ServiceError("VALIDATION_ERROR", "分页游标无效。", 422)
        return ids.index(item_id) + 1
