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
    return JSONResponse(
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

