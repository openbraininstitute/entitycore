"""Request context middleware."""

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.context import request_context
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
        ctx = {"request_id": request_id, "user_id": ""}
        request_context.set(ctx)

        try:
            response = await call_next(request)
        except Exception:
            process_time = time.perf_counter() - start_time
            L.error(
                "{} {}",
                request.method,
                str(request.url),
                client=request.client.host if request.client else "-",
                status_code=500,
                process_time=f"{process_time:.3f}",
                forwarded_for=request.headers.get(HeaderKey.forwarded_for, ""),
            )
            raise

        process_time = time.perf_counter() - start_time
        response.headers[HeaderKey.process_time] = f"{process_time:.3f}"
        response.headers[HeaderKey.request_id] = request_id

        L.info(
            "{} {}",
            request.method,
            str(request.url),
            client=request.client.host if request.client else "-",
            status_code=response.status_code,
            process_time=f"{process_time:.3f}",
            forwarded_for=request.headers.get(HeaderKey.forwarded_for, ""),
        )

        return response
