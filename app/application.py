import asyncio
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

import httpx
from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.db.session import configure_database_session_manager
from app.dependencies.common import forbid_extra_query_params
from app.errors import ApiError, ApiErrorCode
from app.logger import L
from app.routers import router
from app.schemas.api import ErrorResponse
from app.schemas.types import HeaderKey
from app.utils.uuid import create_uuid


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[dict[str, Any]]:
    """Execute actions on server startup and shutdown."""
    L.info(
        "Starting application [PID={}, CPU_COUNT={}, ENVIRONMENT={}]",
        os.getpid(),
        os.cpu_count(),
        settings.ENVIRONMENT,
    )
    database_session_manager = configure_database_session_manager()
    http_client = httpx.Client()
    try:
        yield {
            "database_session_manager": database_session_manager,
            "http_client": http_client,
        }
    except asyncio.CancelledError as err:
        # this can happen if the task is cancelled without sending SIGINT
        L.info("Ignored {} in lifespan", err)
    finally:
        database_session_manager.close()
        http_client.close()  # noqa: ASYNC212
        L.info("Stopping application")


async def api_error_handler(request: Request, exception: ApiError) -> Response:
    """Handle API errors to be returned to the client."""
    err_content = ErrorResponse(
        message=exception.message,
        error_code=exception.error_code,
        details=exception.details,
    )
    L.warning(
        "API error in {} {}: {}, cause: {}",
        request.method,
        request.url,
        err_content,
        exception.__cause__,
    )
    return Response(
        media_type="application/json",
        status_code=int(exception.http_status_code),
        content=err_content.model_dump_json(),
    )


async def validation_exception_handler(
    request: Request, exception: RequestValidationError
) -> Response:
    """Override the default handler for RequestValidationError."""
    details = jsonable_encoder(exception.errors(), exclude={"input"})
    err_content = ErrorResponse(
        message="Validation error",
        error_code=ApiErrorCode.INVALID_REQUEST,
        details=details,
    )
    L.warning(
        "Validation error in {} {}: {}, cause: {}",
        request.method,
        request.url,
        err_content,
        exception.__cause__,
    )
    return Response(
        media_type="application/json",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=err_content.model_dump_json(),
    )


async def http_exception_handler(request: Request, exception: StarletteHTTPException) -> Response:
    """Handle HTTP exceptions to be returned to the client.

    Without this handler, FastAPI would return a JSON error without logging the details.
    """
    err_content = ErrorResponse(
        message="HTTP error",
        error_code=ApiErrorCode.GENERIC_ERROR,
        details=exception.detail,
    )
    L.warning(
        "HTTP error in {} {}: {}, cause: {}",
        request.method,
        request.url,
        err_content,
        exception.__cause__,
    )
    return Response(
        media_type="application/json",
        status_code=int(exception.status_code),
        content=err_content.model_dump_json(),
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION or "0.0.0",
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
    exception_handlers={
        ApiError: api_error_handler,
        RequestValidationError: validation_exception_handler,
        StarletteHTTPException: http_exception_handler,
    },
    root_path=settings.ROOT_PATH,
    redirect_slashes=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Generate a unique request-id and add it to the response headers."""
    request_id = str(create_uuid())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[HeaderKey.request_id] = request_id
    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Calculate the process time and add it to the response headers."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers[HeaderKey.process_time] = str(process_time)
    return response


app.include_router(
    router,
    responses={
        404: {"description": "Not found", "model": ErrorResponse},
        422: {"description": "Validation Error", "model": ErrorResponse},
    },
    dependencies=[Depends(forbid_extra_query_params)],
)
