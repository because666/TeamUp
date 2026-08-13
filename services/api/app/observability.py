from __future__ import annotations

import json
import logging
from time import perf_counter

from fastapi import Request


HTTP_LOGGER = logging.getLogger("teamup.http")


def log_http_request(request: Request, status_code: int, started_at: float) -> None:
    event = {
        "event": "http_request_completed",
        "requestId": request.state.request_id,
        "method": request.method,
        "path": request.url.path,
        "status": status_code,
        "durationMs": round((perf_counter() - started_at) * 1000, 3),
    }
    HTTP_LOGGER.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
