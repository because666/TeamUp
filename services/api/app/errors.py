from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass
class ServiceError(Exception):
    code: str
    message: str
    status_code: int
    details: list[dict[str, str]] | None = None


def error_response(request: Request, error: ServiceError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    response = JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details or [],
            },
            "requestId": request_id,
        },
    )
    if error.code == "RATE_LIMITED":
        retry_after = getattr(request.state, "rate_limit_retry_after", None)
        if retry_after is None and error.details:
            for detail in error.details:
                if detail.get("field") == "retryAfterSeconds":
                    retry_after = detail.get("message")
                    break
        if retry_after is not None:
            response.headers["Retry-After"] = str(retry_after)
    return response
