from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .config import Settings, get_settings
from .database import create_store
from .errors import ServiceError, error_response
from .schemas import (
    Envelope,
    HealthData,
    LoginRequest,
    LogoutData,
    MatchPreferencesData,
    MatchPreferencesPayload,
    MatchPreferencesUpdate,
    ProfileData,
    ProfilePayload,
    ProfileUpdate,
    ProjectAction,
    ProjectData,
    ProjectPayload,
    ProjectUpdate,
    SessionData,
)
from .store import Store
from .wechat import WeChatCodeExchanger, WeChatLoginClient


def envelope(request: Request, data: object, meta: dict[str, object] | None = None) -> dict[str, object]:
    return {"data": data, "meta": meta or {}, "requestId": request.state.request_id}


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise ServiceError("UNAUTHENTICATED", "请先登录后再继续。", 401)
    token = authorization[7:].strip()
    if not token or len(token) > 512:
        raise ServiceError("UNAUTHENTICATED", "登录凭证无效。", 401)
    return token


def make_app(
    settings: Settings | None = None,
    wechat_client: WeChatCodeExchanger | None = None,
    store_override: Store | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    if app_settings.environment in {"staging", "production"} and app_settings.store_backend == "memory":
        raise RuntimeError("The memory store is forbidden in staging and production")
    app_store = store_override or create_store(app_settings)
    wechat_login_client = wechat_client or WeChatLoginClient(app_settings)

    def current_user(authorization: str | None = Header(default=None)) -> str:
        return app_store.user_for_token(bearer_token(authorization))
    app = FastAPI(
        title="TeamUp API",
        version="0.1.0",
        description="TeamUp P0 backend with configurable local memory or MySQL persistence.",
        openapi_tags=[
            {"name": "system"},
            {"name": "auth"},
            {"name": "profile"},
            {"name": "matching"},
            {"name": "projects"},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ServiceError)
    async def handle_service_error(request: Request, exc: ServiceError):
        return error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in error.get("loc", [])), "message": error.get("msg", "invalid value")}
            for error in exc.errors()
        ]
        return error_response(request, ServiceError("VALIDATION_ERROR", "请求参数不符合接口要求。", 422, details))

    api = APIRouter(prefix="/api/v1")

    @api.get("/health/live", tags=["system"], response_model=Envelope[HealthData])
    async def health_live(request: Request):
        return envelope(request, {"status": "ok"})

    @api.get("/health/ready", tags=["system"], response_model=Envelope[HealthData])
    def health_ready(request: Request):
        if not app_store.ready():
            raise ServiceError("DEPENDENCY_NOT_READY", "必要依赖尚未就绪。", 503)
        return envelope(request, {"status": "ready", "storeBackend": app_settings.store_backend})

    @api.post("/auth/wechat/login", tags=["auth"], response_model=Envelope[SessionData])
    async def login(payload: LoginRequest, request: Request):
        if not payload.consentAccepted:
            raise ServiceError("CONSENT_REQUIRED", "请先阅读并同意服务条款与隐私政策。", 422)
        if payload.code.startswith("local:"):
            if app_settings.environment == "production" or not app_settings.allow_local_login:
                raise ServiceError("LOCAL_LOGIN_DISABLED", "本地登录替代方案已禁用。", 401)
            subject = payload.code.removeprefix("local:").strip()
            if not subject or len(subject) > 120:
                raise ServiceError("INVALID_LOGIN_CODE", "登录凭证无效。", 401)
            subject = f"local:{subject}"
        else:
            openid = await wechat_login_client.exchange_code(payload.code)
            subject = f"wechat:{app_settings.wechat_app_id}:{openid}"
        user_id, token, complete = await run_in_threadpool(app_store.login, subject)
        session = SessionData(
            accessToken=token,
            expiresIn=43200,
            userId=user_id,
            profileState="COMPLETE" if complete else "INCOMPLETE",
        )
        return envelope(request, session.model_dump())

    @api.post("/auth/logout", tags=["auth"], response_model=Envelope[LogoutData])
    def logout(request: Request, authorization: str | None = Header(default=None)):
        token = bearer_token(authorization)
        app_store.logout(token)
        return envelope(request, {"loggedOut": True})

    @api.get("/me/profile", tags=["profile"], response_model=Envelope[ProfileData | None])
    def get_profile(request: Request, user_id: str = Depends(current_user)):
        profile = app_store.get_profile(user_id)
        return envelope(request, profile.model_dump(mode="json") if profile else None, {"state": "COMPLETE" if profile else "INCOMPLETE"})

    @api.put("/me/profile", tags=["profile"], response_model=Envelope[ProfileData])
    def save_profile(payload: ProfileUpdate, request: Request, user_id: str = Depends(current_user)):
        profile = app_store.save_profile(user_id, ProfilePayload.model_validate(payload.model_dump(exclude={"version"})), payload.version)
        return envelope(request, profile.model_dump(mode="json"))

    @api.get(
        "/me/match-preferences",
        tags=["matching"],
        response_model=Envelope[MatchPreferencesData | None],
    )
    def get_match_preferences(request: Request, user_id: str = Depends(current_user)):
        preferences = app_store.get_match_preferences(user_id)
        return envelope(
            request,
            preferences.model_dump(mode="json") if preferences else None,
            {"state": "COMPLETE" if preferences else "INCOMPLETE"},
        )

    @api.put(
        "/me/match-preferences",
        tags=["matching"],
        response_model=Envelope[MatchPreferencesData],
    )
    def save_match_preferences(
        payload: MatchPreferencesUpdate,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        preferences = app_store.save_match_preferences(
            user_id,
            MatchPreferencesPayload.model_validate(payload.model_dump(exclude={"version"})),
            payload.version,
        )
        return envelope(request, preferences.model_dump(mode="json"))

    @api.post("/projects", tags=["projects"], response_model=Envelope[ProjectData])
    def create_project(payload: ProjectPayload, request: Request, user_id: str = Depends(current_user)):
        project = app_store.create_project(user_id, payload)
        return envelope(request, project.model_dump(mode="json"))

    @api.get("/projects/{project_id}", tags=["projects"], response_model=Envelope[ProjectData])
    def get_project(project_id: str, request: Request, user_id: str = Depends(current_user)):
        project = app_store.get_project(project_id)
        if project.status == "DRAFT" and project.ownerId != user_id:
            raise ServiceError("RESOURCE_NOT_FOUND", "项目不存在或不可见。", 404)
        return envelope(request, project.model_dump(mode="json"))

    @api.patch("/projects/{project_id}", tags=["projects"], response_model=Envelope[ProjectData])
    def update_project(project_id: str, payload: ProjectUpdate, request: Request, user_id: str = Depends(current_user)):
        project = app_store.update_project(user_id, project_id, payload)
        return envelope(request, project.model_dump(mode="json"))

    @api.post("/projects/{project_id}/publish", tags=["projects"], response_model=Envelope[ProjectData])
    def publish_project(project_id: str, payload: ProjectAction, request: Request, user_id: str = Depends(current_user)):
        project = app_store.publish_project(user_id, project_id, payload.version)
        return envelope(request, project.model_dump(mode="json"))

    @api.post("/projects/{project_id}/close", tags=["projects"], response_model=Envelope[ProjectData])
    def close_project(project_id: str, payload: ProjectAction, request: Request, user_id: str = Depends(current_user)):
        project = app_store.close_project(user_id, project_id, payload.version)
        return envelope(request, project.model_dump(mode="json"))

    @api.get("/projects", tags=["projects"], response_model=Envelope[list[ProjectData]])
    def list_projects(
        request: Request,
        user_id: str = Depends(current_user),
        status: str = Query(default="PUBLISHED", pattern="^(PUBLISHED|CLOSED)$"),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None),
    ):
        del user_id
        projects, next_cursor = app_store.list_projects(status, limit, cursor)
        return envelope(request, [project.model_dump(mode="json") for project in projects], {"nextCursor": next_cursor, "hasMore": next_cursor is not None})

    app.include_router(api)
    return app


app = make_app()
