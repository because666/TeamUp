from __future__ import annotations

import logging
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from .config import Settings
from .errors import ServiceError


class WeChatCodeExchanger(Protocol):
    async def exchange_code(self, code: str) -> str: ...


class SensitiveValueFilter(logging.Filter):
    def __init__(self, *values: str) -> None:
        super().__init__()
        self._values = tuple(value for value in values if value)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for value in self._values:
            message = message.replace(value, "[REDACTED]")
        record.msg = message
        record.args = ()
        return True


class WeChatLoginClient:
    """Exchanges a one-time mini-program code without retaining session_key."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        if not settings.wechat_session_endpoint.startswith("https://"):
            raise ValueError("WeChat session endpoint must use HTTPS")
        endpoint_host = urlparse(settings.wechat_session_endpoint).hostname
        if settings.environment in {"staging", "production"} and endpoint_host != "api.weixin.qq.com":
            raise ValueError("Staging and production must use the official WeChat API host")
        self._settings = settings
        self._transport = transport

    async def exchange_code(self, code: str) -> str:
        if not self._settings.wechat_app_id or not self._settings.wechat_app_secret:
            raise ServiceError("WECHAT_NOT_CONFIGURED", "微信登录服务尚未配置。", 503)

        sensitive_filter = SensitiveValueFilter(
            self._settings.wechat_app_id,
            self._settings.wechat_app_secret,
            self._settings.wechat_proxy_url,
            code,
        )
        external_loggers = tuple(
            logging.getLogger(name)
            for name in (
                "httpx",
                "httpcore",
                "httpcore.connection",
                "httpcore.http11",
                "httpcore.http2",
                "httpcore.proxy",
            )
        )
        for logger in external_loggers:
            logger.addFilter(sensitive_filter)
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.wechat_timeout_seconds,
                transport=self._transport,
                proxy=self._settings.wechat_proxy_url or None,
                trust_env=False,
            ) as client:
                response = await client.get(
                    self._settings.wechat_session_endpoint,
                    params={
                        "appid": self._settings.wechat_app_id,
                        "secret": self._settings.wechat_app_secret,
                        "js_code": code,
                        "grant_type": "authorization_code",
                    },
                )
                response.raise_for_status()
                result: Any = response.json()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError, ValueError):
            raise ServiceError("EXTERNAL_SERVICE_UNAVAILABLE", "微信登录服务暂时不可用。", 503) from None
        finally:
            for logger in external_loggers:
                logger.removeFilter(sensitive_filter)

        if not isinstance(result, dict):
            raise ServiceError("EXTERNAL_SERVICE_UNAVAILABLE", "微信登录服务返回了无效响应。", 503)

        error_code = result.get("errcode")
        if isinstance(error_code, str) and error_code.lstrip("-").isdigit():
            error_code = int(error_code)
        if error_code not in (None, 0, "0"):
            if error_code in {40029, 40163}:
                raise ServiceError("INVALID_LOGIN_CODE", "微信登录凭证无效或已使用。", 401)
            if error_code in {45011, 45009}:
                raise ServiceError("RATE_LIMITED", "登录请求过于频繁，请稍后再试。", 429)
            if error_code in {-1, 40013, 40125}:
                raise ServiceError("EXTERNAL_SERVICE_UNAVAILABLE", "微信登录服务暂时不可用。", 503)
            raise ServiceError("WECHAT_LOGIN_FAILED", "微信登录校验失败。", 502)

        openid = result.get("openid")
        session_key = result.get("session_key")
        if not isinstance(openid, str) or not openid or not isinstance(session_key, str) or not session_key:
            raise ServiceError("EXTERNAL_SERVICE_UNAVAILABLE", "微信登录服务返回了不完整身份信息。", 503)
        return openid
