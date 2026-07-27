import pytest
from sqlalchemy import text

from app.db.session import DatabaseSessionManager


@pytest.fixture
def manager(session_client):
    """A fresh DatabaseSessionManager using the same engine URL as the app, but independent."""
    url = session_client.app.state.database_session_manager.engine.url
    m = DatabaseSessionManager()
    m.initialize(str(url))
    yield m
    m.close()


def test_session_commits_on_success(manager):
    with manager.session() as session:
        result = session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_session_rollback_on_exception(manager):
    err = "forced error"
    with pytest.raises(RuntimeError), manager.session():
        raise RuntimeError(err)
