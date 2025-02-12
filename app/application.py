import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.db.session import configure_database_session_manager
from app.errors import ApiError, ApiErrorCode
from app.logger import L
from app.routers import router
from app.schemas.api import ErrorResponse


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
    try:
        yield {"database_session_manager": database_session_manager}
    except asyncio.CancelledError as err:
        # this can happen if the task is cancelled without sending SIGINT
        L.info("Ignored {} in lifespan", err)
    finally:
        database_session_manager.close()
        L.info("Stopping application")


async def api_error_handler(request: Request, exception: ApiError) -> Response:
    """Handle API errors to be returned to the client."""
    err_content = ErrorResponse(
        message=exception.message,
        error_code=exception.error_code,
        details=exception.details,
    )
    L.warning("API error in {} {}: {}", request.method, request.url, err_content)
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
    L.warning("Validation error in {} {}: {}", request.method, request.url, err_content)
    return Response(
        media_type="application/json",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
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
    },
    root_path=settings.ROOT_PATH,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    router,
)
