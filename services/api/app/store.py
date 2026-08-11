from copy import deepcopy
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import RLock
from uuid import uuid4

from .errors import ServiceError
from .schemas import ProfileData, ProfilePayload, ProjectData, ProjectPayload, ProjectUpdate, RoleData


def now_utc() -> datetime:
    return datetime.now(UTC)


class MemoryStore:
    """Local/test persistence adapter; production must replace this with MySQL."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.users_by_subject: dict[str, str] = {}
        self.sessions: dict[str, tuple[str, datetime]] = {}
        self.profiles: dict[str, ProfileData] = {}
        self.projects: dict[str, ProjectData] = {}

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

    def create_project(self, user_id: str, payload: ProjectPayload) -> ProjectData:
        with self._lock:
            timestamp = now_utc()
            project_id = f"prj_{uuid4().hex}"
            data = ProjectData.model_validate(
                {
                    **payload.model_dump(),
                    "id": project_id,
                    "ownerId": user_id,
                    "status": "DRAFT",
                    "version": 1,
                    "publishedAt": None,
                    "createdAt": timestamp,
                    "updatedAt": timestamp,
                    "roles": [{**role.model_dump(), "id": f"role_{uuid4().hex}"} for role in payload.roles],
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
                    **payload.model_dump(exclude={"version"}),
                    "id": project.id,
                    "ownerId": project.ownerId,
                    "status": project.status,
                    "version": project.version + 1,
                    "publishedAt": project.publishedAt,
                    "createdAt": project.createdAt,
                    "updatedAt": timestamp,
                    "roles": [
                        {
                            **role.model_dump(),
                            "id": project.roles[index].id if index < len(project.roles) else f"role_{uuid4().hex}",
                        }
                        for index, role in enumerate(payload.roles)
                    ],
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

