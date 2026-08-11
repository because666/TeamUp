import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    store_backend: str = "memory"
    allow_local_login: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("TEAMUP_ENVIRONMENT", "local")
    store_backend = os.getenv("TEAMUP_STORE_BACKEND", "memory")
    allow_local_login = os.getenv("TEAMUP_ALLOW_LOCAL_LOGIN", "true").lower() == "true"
    cors_origins = os.getenv("TEAMUP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    if environment not in {"local", "test", "staging", "production"}:
        raise ValueError("TEAMUP_ENVIRONMENT must be local, test, staging, or production")
    if store_backend != "memory":
        raise ValueError("Only the memory store is implemented in the backend foundation")
    return Settings(environment, store_backend, allow_local_login, cors_origins)
