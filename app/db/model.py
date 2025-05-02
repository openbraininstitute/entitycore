"""Database session utils."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import L


class DatabaseSessionManager:
    """DatabaseSessionManager."""

    def __init__(self) -> None:
        """Init the manager."""
        self._engine: Engine | None = None

    def initialize(self, url: str, **kwargs) -> None:
        """Initialize the database engine."""
        if self._engine:
            err = "DB engine already initialized"
            raise RuntimeError(err)
        self._engine = create_engine(url, **kwargs)
        L.info("DB engine has been initialized")

    def close(self) -> None:
        """Shut down the database engine."""
        if not self._engine:
            err = "DB engine not initialized"
            raise RuntimeError(err)
        self._engine.dispose()
        self._engine = None
        L.info("DB engine has been closed")

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a new database session."""
        if not self._engine:
            err = "DB engine not initialized"
            raise RuntimeError(err)
        with Session(
            self._engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        ) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            else:
                session.commit()


def configure_database_session_manager(**kwargs) -> DatabaseSessionManager:
    database_session_manager = DatabaseSessionManager()
    database_session_manager.initialize(
        url=settings.DB_URI,
        **{
            "pool_size": settings.DB_POOL_SIZE,
            "pool_pre_ping": settings.DB_POOL_PRE_PING,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            **kwargs,
        },
    )
    return database_session_manager


