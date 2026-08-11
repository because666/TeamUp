import logging

import httpx
import pytest

from app.config import Settings
from app.errors import ServiceError
from app.main import make_app
from app.wechat import SensitiveValueFilter, WeChatLoginClient


class FakeWeChatClient:
    async def exchange_code(self, code: str) -> str:
        assert code == "wx-code"
        return "openid-test-user"


class FailingWeChatClient:
    async def exchange_code(self, code: str) -> str:
        raise ServiceError("INVALID_LOGIN_CODE", "微信登录凭证无效或已使用。", 401)


class CountingWeChatClient:
    def __init__(self) -> None:
        self.calls = 0

    async def exchange_code(self, code: str) -> str:
        self.calls += 1
        return "openid-never-used"


def test_real_login_creates_platform_session_without_session_key() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(
        make_app(
            Settings(environment="test", allow_local_login=False, wechat_app_id="wx-app", wechat_app_secret="wx-secret"),
            wechat_client=FakeWeChatClient(),
        )
    )
    response = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "wx-code", "consentAccepted": True},
    )
    assert response.status_code == 200
    assert response.json()["data"]["profileState"] == "INCOMPLETE"
    assert "session_key" not in response.json()["data"]
    second = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "wx-code", "consentAccepted": True},
    )
    assert second.json()["data"]["userId"] == response.json()["data"]["userId"]


def test_wechat_and_local_subject_namespaces_are_isolated() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(
        make_app(
            Settings(environment="test", allow_local_login=True, wechat_app_id="wx-app", wechat_app_secret="wx-secret"),
            wechat_client=FakeWeChatClient(),
        )
    )
    wechat_user = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "wx-code", "consentAccepted": True},
    ).json()["data"]["userId"]
    local_user = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:openid-test-user", "consentAccepted": True},
    ).json()["data"]["userId"]
    assert wechat_user != local_user


def test_real_login_maps_wechat_error() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(
        make_app(Settings(environment="test", allow_local_login=False), wechat_client=FailingWeChatClient())
    )
    response = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "wx-code", "consentAccepted": True},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_LOGIN_CODE"


def test_consent_is_checked_before_wechat_call() -> None:
    from fastapi.testclient import TestClient

    wechat_client = CountingWeChatClient()
    client = TestClient(make_app(Settings(environment="test"), wechat_client=wechat_client))
    response = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "wx-code", "consentAccepted": False},
    )
    assert response.status_code == 422
    assert wechat_client.calls == 0


@pytest.mark.anyio
async def test_wechat_client_exchanges_code_and_discards_session_key() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"openid": "openid-real", "session_key": "secret-session-key"})

    settings = Settings(
        environment="test",
        wechat_app_id="wx-app",
        wechat_app_secret="wx-secret",
        wechat_session_endpoint="https://wechat.test/jscode2session",
    )
    client = WeChatLoginClient(settings, transport=httpx.MockTransport(handler))
    assert await client.exchange_code("one-time-code") == "openid-real"
    assert requests[0].url.params["appid"] == "wx-app"
    assert requests[0].url.params["js_code"] == "one-time-code"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_status"),
    [
        ({"errcode": 40029, "errmsg": "invalid code"}, "INVALID_LOGIN_CODE", 401),
        ({"errcode": 45011, "errmsg": "frequency limit"}, "RATE_LIMITED", 429),
        ({"openid": "missing-session-key"}, "EXTERNAL_SERVICE_UNAVAILABLE", 503),
    ],
)
async def test_wechat_client_rejects_failed_or_incomplete_responses(
    payload: dict[str, object], expected_code: str, expected_status: int
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    settings = Settings(
        environment="test",
        wechat_app_id="wx-app",
        wechat_app_secret="wx-secret",
        wechat_session_endpoint="https://wechat.test/jscode2session",
    )
    client = WeChatLoginClient(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(ServiceError) as raised:
        await client.exchange_code("one-time-code")
    assert raised.value.code == expected_code
    assert raised.value.status_code == expected_status


@pytest.mark.anyio
async def test_wechat_client_requires_server_credentials() -> None:
    client = WeChatLoginClient(Settings(environment="test"))
    with pytest.raises(ServiceError) as raised:
        await client.exchange_code("one-time-code")
    assert raised.value.code == "WECHAT_NOT_CONFIGURED"


@pytest.mark.anyio
async def test_wechat_timeout_does_not_expose_request_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    settings = Settings(
        environment="test",
        wechat_app_id="wx-app",
        wechat_app_secret="wx-secret",
        wechat_session_endpoint="https://wechat.test/jscode2session",
    )
    client = WeChatLoginClient(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(ServiceError) as raised:
        await client.exchange_code("one-time-code")
    assert raised.value.code == "EXTERNAL_SERVICE_UNAVAILABLE"
    assert raised.value.__cause__ is None


def test_production_only_allows_official_wechat_host() -> None:
    settings = Settings(
        environment="production",
        store_backend="memory",
        wechat_app_id="wx-app",
        wechat_app_secret="wx-secret",
        wechat_session_endpoint="https://example.invalid/jscode2session",
    )
    with pytest.raises(ValueError, match="official WeChat API host"):
        WeChatLoginClient(settings)


def test_sensitive_value_filter_redacts_credentials_and_code() -> None:
    record = logging.LogRecord(
        "httpx",
        logging.INFO,
        __file__,
        1,
        "GET https://wechat.test?appid=wx-app&secret=wx-secret&js_code=wx-code",
        (),
        None,
    )
    assert SensitiveValueFilter("wx-app", "wx-secret", "wx-code").filter(record)
    message = record.getMessage()
    assert "wx-app" not in message
    assert "wx-secret" not in message
    assert "wx-code" not in message
