"""Database session utils."""

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import L

_test_session_var: contextvars.ContextVar[Session | None] = contextvars.ContextVar(
    "_test_session_var", default=None
)


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

    @property
    def engine(self) -> Engine:
        """The database engine."""
        if not self._engine:
            err = "DB engine not initialized"
            raise RuntimeError(err)
        return self._engine

    @staticmethod
    @contextmanager
    def override_session(session: Session) -> Iterator[None]:
        """Override the session used by all requests, for use in tests only."""
        token = _test_session_var.set(session)
        try:
            yield
        finally:
            _test_session_var.reset(token)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a new database session."""
        if (test_session := _test_session_var.get()) is not None:
            # expire before each request so objects inserted by test setup are reloaded
            # fresh from DB, preventing stale cached relationships (e.g. selectin) from
            # being seen by the request handler
            test_session.expire_all()
            with test_session.begin_nested():
                yield test_session
            return
        with Session(
            self.engine,
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
