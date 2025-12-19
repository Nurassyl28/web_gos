from __future__ import annotations

import logging
import time
from collections import deque
from typing import Deque

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger("app.middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.history: dict[str, Deque[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        limit = settings.rate_limit_requests
        window = settings.rate_limit_window_seconds
        timestamps = self.history.setdefault(client, deque())
        while timestamps and now - timestamps[0] > window:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        timestamps.append(now)
        response = await call_next(request)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header = request.headers.get("content-length")
        max_size = getattr(settings, "max_request_size", 0)
        if header and header.isdigit():
            if int(header) > max_size and max_size > 0:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request body too large",
                )
        return await call_next(request)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.require_https:
            return await call_next(request)
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        scheme = request.url.scheme or ""
        if forwarded_proto.lower() != "https" and scheme.lower() != "https":
            logger.warning("Rejected non-HTTPS request from %s", request.client)
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail="HTTPS required",
            )
        return await call_next(request)
