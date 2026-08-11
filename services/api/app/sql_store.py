from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import Engine, Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker

from .db_models import (
    ProfileRow,
    ProfileScenarioRow,
    ProfileSkillRow,
    ProjectRoleRow,
    ProjectRoleSkillRow,
    ProjectRow,
    SessionRow,
    UserRow,
)
from .errors import ServiceError
from .schemas import ProfileData, ProfilePayload, ProjectData, ProjectPayload, ProjectUpdate, RoleData


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
            existing_ids = [role.id for role in row.roles]
            row.roles.clear()
            session.flush()
            self._replace_roles(row, payload.roles, existing_ids)
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
    def _project_query() -> Select[tuple[ProjectRow]]:
        return select(ProjectRow).options(selectinload(ProjectRow.roles).selectinload(ProjectRoleRow.skills))

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
    def _replace_roles(row: ProjectRow, payload_roles: list, existing_ids: list[str] | None = None) -> None:
        existing_ids = existing_ids or []
        row.roles = [
            ProjectRoleRow(
                id=existing_ids[index] if index < len(existing_ids) else f"role_{uuid4().hex}",
                position=index,
                name=role.name,
                headcount=role.headcount,
                hours_per_week=role.hoursPerWeek,
                description=role.description,
                status=role.status,
                skills=[
                    ProjectRoleSkillRow(position=skill_index, skill_name=skill)
                    for skill_index, skill in enumerate(role.skills)
                ],
            )
            for index, role in enumerate(payload_roles)
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
    def _project_data(row: ProjectRow) -> ProjectData:
        roles = sorted(row.roles, key=lambda item: item.position)
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
    def _require_owner(row: ProjectRow | None, user_id: str) -> None:
        if row is None:
            raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
        if row.owner_id != user_id:
            raise ServiceError("FORBIDDEN", "你没有权限操作该项目。", 403)
