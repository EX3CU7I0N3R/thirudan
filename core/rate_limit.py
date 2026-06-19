from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.utils import encode_token


@dataclass(frozen=True)
class RateLimitConfig:
    max_requests: int = 25
    window_seconds: int = 60


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app: object, config: RateLimitConfig | None = None) -> None:
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        now = time.monotonic()
        key = self._key_for(request)
        window = self.requests[key]

        while window and now - window[0] > self.config.window_seconds:
            window.popleft()

        if not window:
            self.requests.pop(key, None)
            window = self.requests[key]

        if len(window) >= self.config.max_requests:
            return Response(
                content='{"error":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
            )

        window.append(now)
        return await call_next(request)

    @staticmethod
    def _key_for(request: Request) -> str:
        token = request.headers.get("X-CSRF-Token")
        if token:
            return encode_token(token)
        return request.client.host if request.client else "unknown"
