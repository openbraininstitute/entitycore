"""Request context middleware."""

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.context import RequestContext, request_context_provider
from app.logger import L
from app.schemas.types import HeaderKey
from app.utils.uuid import create_uuid

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to initialize request context and log access."""

    async def dispatch(  # noqa: PLR6301
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Set request context and log access."""
        start_time = time.perf_counter()
        request_id = str(create_uuid())
        ctx = RequestContext(request_id=request_id)
        request_context_provider.set(ctx)

        try:
            response = await call_next(request)
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
        response.headers[HeaderKey.process_time] = f"{process_time:.3f}"
        response.headers[HeaderKey.request_id] = request_id
        response_size = response.headers.get(HeaderKey.content_length)
        route = request.scope.get("route")
        route_template = route.path if route else None

        L.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            route_template=route_template,
            status_code=response.status_code,
            status_class=response.status_code // 100,
            process_time_ms=round(process_time * 1000),
            response_size=int(response_size) if response_size else None,
            client=request.client.host if request.client else "",
            forwarded_for=request.headers.get(HeaderKey.forwarded_for, ""),
            user_agent=request.headers.get(HeaderKey.user_agent, ""),
        )

        return response
