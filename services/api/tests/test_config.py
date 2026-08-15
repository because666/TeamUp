import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_persistent_environments_reject_memory_store(monkeypatch, environment: str) -> None:
    monkeypatch.setenv("TEAMUP_ENVIRONMENT", environment)
    monkeypatch.setenv("TEAMUP_STORE_BACKEND", "memory")
    monkeypatch.delenv("TEAMUP_DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="must be mysql"):
        get_settings()


def test_local_environment_keeps_explicit_memory_store(monkeypatch) -> None:
    monkeypatch.setenv("TEAMUP_ENVIRONMENT", "local")
    monkeypatch.setenv("TEAMUP_STORE_BACKEND", "memory")
    monkeypatch.delenv("TEAMUP_DATABASE_URL", raising=False)

    settings = get_settings()

    assert settings.environment == "local"
    assert settings.store_backend == "memory"
