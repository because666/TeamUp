from copy import deepcopy
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import RLock
from typing import Protocol
from uuid import uuid4

from .errors import ServiceError
from .schemas import (
    BlockData,
    InvitationAcceptData,
    InvitationData,
    MatchPreferencesData,
    MatchPreferencesPayload,
    ProfileData,
    ProfilePayload,
    ProjectData,
    ProjectMemberData,
    ProjectPayload,
    ProjectUpdate,
    RoleData,
    RolePayload,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


class Store(Protocol):
    def login(self, subject: str) -> tuple[str, str, bool]: ...
    def user_for_token(self, token: str) -> str: ...
    def logout(self, token: str) -> None: ...
    def create_block(self, blocker_id: str, blocked_id: str) -> BlockData: ...
    def remove_block(self, blocker_id: str, blocked_id: str) -> bool: ...
    def users_blocked(self, first_user_id: str, second_user_id: str) -> bool: ...
    def create_invitation(
        self, inviter_id: str, project_id: str, role_id: str, invitee_id: str
    ) -> InvitationData: ...
    def accept_invitation(self, invitee_id: str, invitation_id: str) -> InvitationAcceptData: ...
    def reject_invitation(self, invitee_id: str, invitation_id: str) -> InvitationData: ...
    def get_profile(self, user_id: str) -> ProfileData | None: ...
    def save_profile(self, user_id: str, payload: ProfilePayload, version: int | None) -> ProfileData: ...
    def get_match_preferences(self, user_id: str) -> MatchPreferencesData | None: ...
    def save_match_preferences(
        self, user_id: str, payload: MatchPreferencesPayload, version: int | None
    ) -> MatchPreferencesData: ...
    def create_project(self, user_id: str, payload: ProjectPayload) -> ProjectData: ...
    def get_project(self, project_id: str) -> ProjectData: ...
    def update_project(self, user_id: str, project_id: str, payload: ProjectUpdate) -> ProjectData: ...
    def publish_project(self, user_id: str, project_id: str, version: int) -> ProjectData: ...
    def close_project(self, user_id: str, project_id: str, version: int) -> ProjectData: ...
    def add_project_member(self, project_id: str, role_id: str, user_id: str) -> ProjectMemberData: ...
    def list_project_members(self, requester_id: str, project_id: str) -> list[ProjectMemberData]: ...
    def list_projects(self, status: str, limit: int, cursor: str | None) -> tuple[list[ProjectData], str | None]: ...
    def ready(self) -> bool: ...


class MemoryStore:
    """Local/test persistence adapter; production must replace this with MySQL."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.users_by_subject: dict[str, str] = {}
        self.sessions: dict[str, tuple[str, datetime]] = {}
        self.blocks: dict[tuple[str, str], BlockData] = {}
        self.invitations: dict[str, InvitationData] = {}
        self.profiles: dict[str, ProfileData] = {}
        self.match_preferences: dict[str, MatchPreferencesData] = {}
        self.projects: dict[str, ProjectData] = {}
        self.project_members: dict[str, ProjectMemberData] = {}

    def ready(self) -> bool:
        return True

    def login(self, subject: str) -> tuple[str, str, bool]:
        with self._lock:
            user_id = self.users_by_subject.setdefault(subject, f"usr_{uuid4().hex}")
            token = f"tu_{token_urlsafe(32)}"
            self.sessions[token] = (user_id, now_utc() + timedelta(hours=12))
            return user_id, token, user_id in self.profiles

    def user_for_token(self, token: str) -> str:
        with self._lock:
            session = self.sessions.get(token)
            if not session or session[1] <= now_utc():
                self.sessions.pop(token, None)
                raise ServiceError("SESSION_EXPIRED", "登录状态已失效，请重新登录。", 401)
            return session[0]

    def logout(self, token: str) -> None:
        with self._lock:
            self.sessions.pop(token, None)

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

    def get_profile(self, user_id: str) -> ProfileData | None:
        with self._lock:
            return deepcopy(self.profiles.get(user_id))

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

    def get_project(self, project_id: str) -> ProjectData:
        with self._lock:
            project = self.projects.get(project_id)
            if not project:
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

    def list_projects(self, status: str, limit: int, cursor: str | None) -> tuple[list[ProjectData], str | None]:
        with self._lock:
            projects = sorted(
                (project for project in self.projects.values() if project.status == status),
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
