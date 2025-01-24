import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import DatabaseSessionManager, configure_database_session_manager
from app.logger import L
from app.routers import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[dict[str, Any]]:
    """Execute actions on server startup and shutdown."""
    L.info(
        "Starting application [PID=%s, CPU_COUNT=%s, ENVIRONMENT=%s]",
        os.getpid(),
        os.cpu_count(),
        settings.ENVIRONMENT,
    )
    database_session_manager = configure_database_session_manager()
    try:
        yield {"database_session_manager": database_session_manager}
    except asyncio.CancelledError as err:
        # this can happen if the task is cancelled without sending SIGINT
        L.info("Ignored %s in lifespan", err)
    finally:
        database_session_manager.close()
        L.info("Stopping application")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    router,
)
