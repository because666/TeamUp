from __future__ import annotations

from re import fullmatch
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .config import Settings, get_settings
from .database import create_store
from .errors import ServiceError, error_response
from .observability import log_http_request
from .rate_limit import InMemoryRateLimiter
from .schemas import (
    AccountDeletionRequestData,
    BlockData,
    BlockRequest,
    ConversationCreateRequest,
    ConversationData,
    Envelope,
    HealthData,
    InvitationAcceptData,
    InvitationCreateRequest,
    InvitationData,
    LoginRequest,
    LogoutData,
    MatchPreferencesData,
    MatchPreferencesPayload,
    MatchPreferencesUpdate,
    MatchResultData,
    RecommendationImpressionData,
    RecommendationImpressionRequest,
    ReportData,
    ReportRequest,
    MessageData,
    MessageSendRequest,
    ProfileData,
    ProfilePayload,
    ProfileUpdate,
    PublicProfileData,
    ProjectAction,
    ProjectData,
    ProjectMemberData,
    ProjectPayload,
    ProjectUpdate,
    SessionData,
    UnblockData,
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
    rate_limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    if app_settings.environment in {"staging", "production"} and app_settings.store_backend == "memory":
        raise RuntimeError("The memory store is forbidden in staging and production")
    app_store = store_override or create_store(app_settings)
    app_rate_limiter = rate_limiter or InMemoryRateLimiter()
    wechat_login_client = wechat_client or WeChatLoginClient(app_settings)

    def current_user(authorization: str | None = Header(default=None)) -> str:
        return app_store.user_for_token(bearer_token(authorization))

    def enforce_rate_limit(scope: str, key: str, request: Request) -> None:
        retry_after = app_rate_limiter.check(scope, key)
        if retry_after is None:
            return
        request.state.rate_limit_retry_after = retry_after
        raise ServiceError(
            "RATE_LIMITED",
            "请求过于频繁，请稍后重试。",
            429,
            [{"field": "retryAfterSeconds", "message": str(retry_after)}],
        )
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
            {"name": "team"},
            {"name": "messages"},
            {"name": "safety"},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        started_at = perf_counter()
        candidate_request_id = request.headers.get("X-Request-ID")
        request.state.request_id = (
            candidate_request_id
            if candidate_request_id
            and len(candidate_request_id) <= 128
            and fullmatch(r"[A-Za-z0-9._:-]+", candidate_request_id)
            else f"req_{uuid4().hex}"
        )
        try:
            response = await call_next(request)
        except Exception:
            log_http_request(request, 500, started_at)
            raise
        response.headers["X-Request-ID"] = request.state.request_id
        log_http_request(request, response.status_code, started_at)
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

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        # Keep internal exception details out of the public response.
        return error_response(request, ServiceError("INTERNAL_ERROR", "服务暂时不可用，请稍后重试。", 500))

    api = APIRouter(prefix="/api/v1")

    @api.get("/health/live", tags=["system"], response_model=Envelope[HealthData])
    async def health_live(request: Request):
        return envelope(request, {"status": "ok"})

    @api.get("/health/ready", tags=["system"], response_model=Envelope[HealthData])
    def health_ready(request: Request):
        try:
            ready = app_store.ready()
        except Exception:
            ready = False
        if not ready:
            raise ServiceError("DEPENDENCY_NOT_READY", "必要依赖尚未就绪。", 503)
        return envelope(request, {"status": "ready", "storeBackend": app_settings.store_backend})

    @api.post("/auth/wechat/login", tags=["auth"], response_model=Envelope[SessionData])
    async def login(payload: LoginRequest, request: Request):
        client_host = request.client.host if request.client else "unknown"
        enforce_rate_limit("auth.login", client_host, request)
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
        app_store.logout(token, request.state.request_id)
        return envelope(request, {"loggedOut": True})

    @api.post(
        "/account/deletion-requests",
        tags=["auth"],
        response_model=Envelope[AccountDeletionRequestData],
    )
    def request_account_deletion(
        request: Request,
        user_id: str = Depends(current_user),
    ):
        deletion_request = app_store.request_account_deletion(user_id, request.state.request_id)
        return envelope(request, deletion_request.model_dump(mode="json"))

    @api.post("/blocks", tags=["safety"], response_model=Envelope[BlockData])
    def create_block(payload: BlockRequest, request: Request, user_id: str = Depends(current_user)):
        block = app_store.create_block(user_id, payload.blockedUserId)
        return envelope(request, block.model_dump(mode="json"))

    @api.post("/reports", tags=["safety"], response_model=Envelope[ReportData])
    def create_report(
        payload: ReportRequest,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        enforce_rate_limit("safety.report", user_id, request)
        report = app_store.create_report(user_id, payload, request.state.request_id)
        return envelope(request, report.model_dump(mode="json"))

    @api.delete("/blocks/{blocked_user_id}", tags=["safety"], response_model=Envelope[UnblockData])
    def remove_block(blocked_user_id: str, request: Request, user_id: str = Depends(current_user)):
        if not blocked_user_id or len(blocked_user_id) > 64:
            raise ServiceError("VALIDATION_ERROR", "用户标识不符合接口要求。", 422)
        removed = app_store.remove_block(user_id, blocked_user_id)
        return envelope(request, {"blockedUserId": blocked_user_id, "removed": removed})

    @api.post("/invitations", tags=["team"], response_model=Envelope[InvitationData])
    def create_invitation(
        payload: InvitationCreateRequest,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        enforce_rate_limit("team.invitation", user_id, request)
        invitation = app_store.create_invitation(
            user_id,
            payload.projectId,
            payload.roleId,
            payload.inviteeUserId,
        )
        return envelope(request, invitation.model_dump(mode="json"))

    @api.post(
        "/invitations/{invitation_id}/accept",
        tags=["team"],
        response_model=Envelope[InvitationAcceptData],
    )
    def accept_invitation(
        invitation_id: str,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        result = app_store.accept_invitation(user_id, invitation_id)
        return envelope(request, result.model_dump(mode="json"))

    @api.post(
        "/invitations/{invitation_id}/reject",
        tags=["team"],
        response_model=Envelope[InvitationData],
    )
    def reject_invitation(
        invitation_id: str,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        invitation = app_store.reject_invitation(user_id, invitation_id)
        return envelope(request, invitation.model_dump(mode="json"))

    @api.post("/conversations", tags=["messages"], response_model=Envelope[ConversationData])
    def create_conversation(
        payload: ConversationCreateRequest,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        conversation = app_store.create_conversation(user_id, payload.projectId, payload.otherUserId)
        return envelope(request, conversation.model_dump(mode="json"))

    @api.get("/conversations", tags=["messages"], response_model=Envelope[list[ConversationData]])
    def list_conversations(
        request: Request,
        user_id: str = Depends(current_user),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
    ):
        conversations, next_cursor = app_store.list_conversations(user_id, limit, cursor)
        return envelope(
            request,
            [conversation.model_dump(mode="json") for conversation in conversations],
            {"nextCursor": next_cursor, "hasMore": next_cursor is not None},
        )

    @api.get(
        "/conversations/{conversation_id}/messages",
        tags=["messages"],
        response_model=Envelope[list[MessageData]],
    )
    def list_messages(
        conversation_id: str,
        request: Request,
        user_id: str = Depends(current_user),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
    ):
        messages, next_cursor = app_store.list_messages(user_id, conversation_id, limit, cursor)
        return envelope(
            request,
            [message.model_dump(mode="json") for message in messages],
            {"nextCursor": next_cursor, "hasMore": next_cursor is not None},
        )

    @api.post(
        "/conversations/{conversation_id}/messages",
        tags=["messages"],
        response_model=Envelope[MessageData],
    )
    def send_message(
        conversation_id: str,
        payload: MessageSendRequest,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        enforce_rate_limit("messages.send", user_id, request)
        message = app_store.send_message(
            user_id,
            conversation_id,
            payload.clientMessageId,
            payload.content,
        )
        return envelope(request, message.model_dump(mode="json"))

    @api.get("/me/profile", tags=["profile"], response_model=Envelope[ProfileData | None])
    def get_profile(request: Request, user_id: str = Depends(current_user)):
        profile = app_store.get_profile(user_id)
        return envelope(request, profile.model_dump(mode="json") if profile else None, {"state": "COMPLETE" if profile else "INCOMPLETE"})

    @api.get("/profiles/{profile_id}", tags=["profile"], response_model=Envelope[PublicProfileData])
    def get_public_profile(profile_id: str, request: Request, user_id: str = Depends(current_user)):
        profile = app_store.get_public_profile(user_id, profile_id)
        return envelope(request, profile.model_dump(mode="json"))

    @api.get("/profiles", tags=["profile"], response_model=Envelope[list[PublicProfileData]])
    def list_public_profiles(
        request: Request,
        user_id: str = Depends(current_user),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
        skill: str | None = Query(default=None, min_length=1, max_length=64),
        direction: str | None = Query(default=None, min_length=1, max_length=64),
        collaborationRole: str | None = Query(default=None, pattern="^(LEADER|MEMBER|FLEXIBLE)$"),
        minHoursPerWeek: int | None = Query(default=None, ge=1, le=40),
        maxHoursPerWeek: int | None = Query(default=None, ge=1, le=40),
    ):
        if minHoursPerWeek is not None and maxHoursPerWeek is not None and minHoursPerWeek > maxHoursPerWeek:
            raise ServiceError("VALIDATION_ERROR", "投入时间范围无效。", 422)
        profiles, next_cursor = app_store.list_public_profiles(
            user_id, limit, cursor, skill, direction, collaborationRole, minHoursPerWeek, maxHoursPerWeek
        )
        return envelope(
            request,
            [profile.model_dump(mode="json") for profile in profiles],
            {"nextCursor": next_cursor, "hasMore": next_cursor is not None},
        )

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

    @api.get(
        "/projects/{project_id}/matches",
        tags=["matching"],
        response_model=Envelope[list[MatchResultData]],
    )
    def project_matches(
        project_id: str,
        request: Request,
        roleId: str = Query(min_length=1, max_length=64),
        user_id: str = Depends(current_user),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
    ):
        results, next_cursor, request_id = app_store.project_matches(user_id, project_id, roleId, limit, cursor)
        return envelope(
            request,
            [result.model_dump(mode="json") for result in results],
            {"recommendationRequestId": request_id, "nextCursor": next_cursor, "hasMore": next_cursor is not None},
        )

    @api.get(
        "/me/project-matches",
        tags=["matching"],
        response_model=Envelope[list[MatchResultData]],
    )
    def user_project_matches(
        request: Request,
        user_id: str = Depends(current_user),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
    ):
        results, next_cursor, request_id = app_store.user_project_matches(user_id, limit, cursor)
        return envelope(
            request,
            [result.model_dump(mode="json") for result in results],
            {"recommendationRequestId": request_id, "nextCursor": next_cursor, "hasMore": next_cursor is not None},
        )

    @api.post(
        "/recommendation-impressions",
        tags=["matching"],
        response_model=Envelope[list[RecommendationImpressionData]],
    )
    def record_recommendation_impressions(
        payload: RecommendationImpressionRequest,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        recorded = app_store.record_recommendation_impressions(user_id, payload)
        return envelope(request, [item.model_dump(mode="json") for item in recorded])

    @api.post("/projects", tags=["projects"], response_model=Envelope[ProjectData])
    def create_project(payload: ProjectPayload, request: Request, user_id: str = Depends(current_user)):
        project = app_store.create_project(user_id, payload)
        return envelope(request, project.model_dump(mode="json"))

    @api.get("/projects/{project_id}", tags=["projects"], response_model=Envelope[ProjectData])
    def get_project(project_id: str, request: Request, user_id: str = Depends(current_user)):
        project = app_store.get_project(project_id, user_id)
        return envelope(request, project.model_dump(mode="json"))

    @api.get(
        "/projects/{project_id}/members",
        tags=["projects"],
        response_model=Envelope[list[ProjectMemberData]],
    )
    def list_project_members(
        project_id: str,
        request: Request,
        user_id: str = Depends(current_user),
    ):
        members = app_store.list_project_members(user_id, project_id)
        return envelope(request, [member.model_dump(mode="json") for member in members])

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
        status: str = Query(default="PUBLISHED", pattern="^PUBLISHED$"),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None),
        direction: str | None = Query(default=None, min_length=1, max_length=64),
        competition: str | None = Query(default=None, min_length=1, max_length=80),
        stage: str | None = Query(default=None, min_length=1, max_length=64),
        skill: str | None = Query(default=None, min_length=1, max_length=64),
    ):
        projects, next_cursor = app_store.list_projects(
            status, limit, cursor, direction, competition, stage, skill, user_id
        )
        return envelope(request, [project.model_dump(mode="json") for project in projects], {"nextCursor": next_cursor, "hasMore": next_cursor is not None})

    @api.get("/me/projects", tags=["projects"], response_model=Envelope[list[ProjectData]])
    def list_my_projects(
        request: Request,
        user_id: str = Depends(current_user),
        status: str | None = Query(default=None, pattern="^(DRAFT|PUBLISHED|CLOSED)$"),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=512),
    ):
        projects, next_cursor = app_store.list_my_projects(user_id, status, limit, cursor)
        return envelope(request, [project.model_dump(mode="json") for project in projects], {"nextCursor": next_cursor, "hasMore": next_cursor is not None})

    app.include_router(api)
    return app


app = make_app()
