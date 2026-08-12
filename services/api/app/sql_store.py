from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import Engine, Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker

from .db_models import (
    BlockRow,
    InvitationRow,
    MatchPreferenceAvailabilitySlotRow,
    MatchPreferenceDirectionRow,
    MatchPreferenceRow,
    ProfileRow,
    ProfileScenarioRow,
    ProfileSkillRow,
    ProjectMemberRow,
    ProjectRoleAvailabilitySlotRow,
    ProjectRoleRow,
    ProjectRoleSkillRow,
    ProjectRow,
    ProjectScenarioRow,
    SessionRow,
    UserRow,
)
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

    def logout(self, token: str) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(select(SessionRow).where(SessionRow.token_digest == token_digest(token)).with_for_update())
            if row is not None and row.revoked_at is None:
                row.revoked_at = db_now()

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

    def get_profile(self, user_id: str) -> ProfileData | None:
        with self._session_factory() as session:
            row = session.scalar(self._profile_query().where(ProfileRow.user_id == user_id))
            return self._profile_data(row) if row else None

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

    def get_project(self, project_id: str) -> ProjectData:
        with self._session_factory() as session:
            row = session.scalar(self._project_query().where(ProjectRow.id == project_id))
            if row is None:
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

    def list_projects(self, status: str, limit: int, cursor: str | None) -> tuple[list[ProjectData], str | None]:
        with self._session_factory() as session:
            sort_time = func.coalesce(ProjectRow.published_at, ProjectRow.created_at)
            query = self._project_query().where(ProjectRow.status == status)
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
    def _require_owner(row: ProjectRow | None, user_id: str) -> None:
        if row is None:
            raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
        if row.owner_id != user_id:
            raise ServiceError("FORBIDDEN", "你没有权限操作该项目。", 403)
