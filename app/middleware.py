"""Request context middleware."""

import time
from dataclasses import dataclass
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.context import RequestContext, request_context_provider
from app.logger import L
from app.schemas.types import HeaderKey
from app.utils.uuid import create_uuid


def _to_ms(seconds: float) -> int:
    return round(seconds * 1000)


@dataclass(slots=True, kw_only=True)
class _ResponseInfo:
    """Response metadata captured from the http.response.start message."""

    # Status sent by ServerErrorMiddleware or uvicorn if the app doesn't send the headers.
    status_code: int = 500
    process_time: float | None = None
    response_size: int | None = None
    content_encoding: str | None = None


class RequestContextMiddleware:
    """Pure ASGI middleware to initialize request context and log access.

    The logged process_time_ms is the time until the response headers are sent (or until the
    failure, if the headers were never sent), and it's the same value of the X-Process-Time header.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize with the ASGI application."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Set request context, add response headers, and log access."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request_id = str(create_uuid())
        request_context_provider.set(RequestContext(request_id=request_id))
        # Only used to read the request metadata: the body is never consumed here.
        request = Request(scope)
        info = _ResponseInfo()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                info.process_time = time.perf_counter() - start_time
                info.status_code = message["status"]
                # Copy the headers to avoid mutating the list owned by the Response object.
                headers = MutableHeaders(raw=list(message.get("headers", [])))
                headers[HeaderKey.process_time] = f"{info.process_time:.3f}"
                headers[HeaderKey.request_id] = request_id
                content_length = headers.get(HeaderKey.content_length)
                info.response_size = int(content_length) if content_length else None
                info.content_encoding = headers.get(HeaderKey.content_encoding)
                message = {**message, "headers": headers.raw}
            await send(message)

        def log_fields() -> dict[str, Any]:
            # None if the app failed before sending the headers
            if (process_time := info.process_time) is None:
                process_time = time.perf_counter() - start_time
            route = scope.get("route")
            return {
                "method": request.method,
                "url": str(request.url),
                "route_template": route.path if route else None,
                "status_code": info.status_code,
                "status_class": info.status_code // 100,
                "process_time_ms": _to_ms(process_time),
                "client": request.client.host if request.client else "",
                "forwarded_for": request.headers.get(HeaderKey.forwarded_for, ""),
                "user_agent": request.headers.get(HeaderKey.user_agent, ""),
            }

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            L.error("request_failed", **log_fields())
            raise

        L.info(
            "request_completed",
            **log_fields(),
            response_size=info.response_size,
            content_encoding=info.content_encoding,
        )
