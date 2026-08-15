import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    store_backend: str = "memory"
    database_url: str = field(default="", repr=False)
    allow_local_login: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    wechat_app_id: str = ""
    wechat_app_secret: str = field(default="", repr=False)
    wechat_proxy_url: str = field(default="", repr=False)
    wechat_session_endpoint: str = "https://api.weixin.qq.com/sns/jscode2session"
    wechat_timeout_seconds: float = 5.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("TEAMUP_ENVIRONMENT", "local")
    store_backend = os.getenv("TEAMUP_STORE_BACKEND", "memory")
    database_url = os.getenv("TEAMUP_DATABASE_URL", "")
    allow_local_login = os.getenv("TEAMUP_ALLOW_LOCAL_LOGIN", "true").lower() == "true"
    cors_origins = os.getenv("TEAMUP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    wechat_app_id = os.getenv("TEAMUP_WECHAT_APP_ID", "")
    wechat_app_secret = os.getenv("TEAMUP_WECHAT_APP_SECRET", "")
    wechat_proxy_url = os.getenv("TEAMUP_WECHAT_PROXY_URL", "")
    wechat_session_endpoint = os.getenv(
        "TEAMUP_WECHAT_SESSION_ENDPOINT",
        "https://api.weixin.qq.com/sns/jscode2session",
    )
    try:
        wechat_timeout_seconds = float(os.getenv("TEAMUP_WECHAT_TIMEOUT_SECONDS", "5"))
    except ValueError as error:
        raise ValueError("TEAMUP_WECHAT_TIMEOUT_SECONDS must be a number") from error
    if not 1 <= wechat_timeout_seconds <= 15:
        raise ValueError("TEAMUP_WECHAT_TIMEOUT_SECONDS must be between 1 and 15")
    if environment not in {"local", "test", "staging", "production"}:
        raise ValueError("TEAMUP_ENVIRONMENT must be local, test, staging, or production")
    if store_backend not in {"memory", "mysql"}:
        raise ValueError("TEAMUP_STORE_BACKEND must be memory or mysql")
    if store_backend == "mysql" and not database_url:
        raise ValueError("TEAMUP_DATABASE_URL is required when TEAMUP_STORE_BACKEND=mysql")
    if environment in {"staging", "production"} and store_backend != "mysql":
        raise ValueError("TEAMUP_STORE_BACKEND must be mysql in staging and production")
    if database_url and not database_url.startswith("mysql+pymysql://"):
        raise ValueError("TEAMUP_DATABASE_URL must use the mysql+pymysql driver")
    return Settings(
        environment=environment,
        store_backend=store_backend,
        database_url=database_url,
        allow_local_login=allow_local_login,
        cors_origins=cors_origins,
        wechat_app_id=wechat_app_id,
        wechat_app_secret=wechat_app_secret,
        wechat_proxy_url=wechat_proxy_url,
        wechat_session_endpoint=wechat_session_endpoint,
        wechat_timeout_seconds=wechat_timeout_seconds,
    )
