from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import app
from app.db.model import Base
from app.db.session import DatabaseSessionManager, configure_database_session_manager


@pytest.fixture(scope="session")
def client():
    """Yield a web client instance.

    The fixture is session-scoped so that the lifespan events are executed only once per session.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def database_session_manager() -> DatabaseSessionManager:
    return configure_database_session_manager()


@pytest.fixture(scope="function")
def db(database_session_manager) -> Iterator[Session]:
    with database_session_manager.session() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def _db_cleanup(db):
    yield
    query = text(f"""TRUNCATE {",".join(Base.metadata.tables)} RESTART IDENTITY CASCADE""")
    db.execute(query)
    db.commit()
