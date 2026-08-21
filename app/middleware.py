"""Request context middleware."""

import time

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings
from app.context import RequestContext, request_context_provider
from app.logger import L
from app.profiling import log_profile_summary, reset_query_log
from app.schemas.types import HeaderKey
from app.utils.uuid import create_uuid


class RequestContextMiddleware:
    """Pure ASGI middleware to initialize request context and log access."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize with the ASGI application."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request_id = str(create_uuid())
        ctx = RequestContext(request_id=request_id)
        request_context_provider.set(ctx)

        if settings.PROFILING_ENABLED:
            reset_query_log()

        request = Request(scope, receive, send)
        status_code: int = 500
        response_size: str | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_size
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = _inject_headers(message, start_time, request_id)
                response_size = _get_header(headers, b"content-length")
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            process_time = time.perf_counter() - start_time
            L.error(
                "request_failed",
                method=request.method,
                url=str(request.url),
                status_code=500,
                status_class=5,
                process_time_ms=round(process_time * 1000),
                client=request.client.host if request.client else "",
                forwarded_for=request.headers.get(HeaderKey.forwarded_for, ""),
                user_agent=request.headers.get(HeaderKey.user_agent, ""),
            )
            raise

        process_time = time.perf_counter() - start_time
        route = scope.get("route")
        route_template = route.path if route else None

        if settings.PROFILING_ENABLED:
            log_profile_summary(request, route_template, process_time)

        L.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            route_template=route_template,
            status_code=status_code,
            status_class=status_code // 100,
            process_time_ms=round(process_time * 1000),
            response_size=int(response_size) if response_size else None,
            client=request.client.host if request.client else "",
            forwarded_for=request.headers.get(HeaderKey.forwarded_for, ""),
            user_agent=request.headers.get(HeaderKey.user_agent, ""),
        )


def _inject_headers(
    message: Message, start_time: float, request_id: str
) -> list[tuple[bytes, bytes]]:
    """Add process-time and request-id headers to the response."""
    headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
    process_time = time.perf_counter() - start_time
    headers.extend(
        [
            (HeaderKey.process_time.encode().lower(), f"{process_time:.3f}".encode()),
            (HeaderKey.request_id.encode().lower(), request_id.encode()),
        ]
    )
    return headers


def _get_header(headers: list[tuple[bytes, bytes]], name: bytes) -> str | None:
    """Extract a header value by lowercase name."""
    for key, value in headers:
        if key.lower() == name:
            return value.decode()
    return None
