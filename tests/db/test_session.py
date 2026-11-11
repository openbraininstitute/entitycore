import pytest
from sqlalchemy import text

from app.config import settings
from app.db import session as test_module


@pytest.fixture
def manager():
    """A fresh DatabaseSessionManager using the same engine URL as the app, but independent."""
    m = test_module.configure_database_session_manager()
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


def test_statement_timeout_is_set_on_connections(manager):
    with manager.engine.connect() as connection:
        value = connection.execute(
            text("SELECT setting FROM pg_settings WHERE name = 'statement_timeout'")
        ).scalar_one()
    assert int(value) == settings.DB_STATEMENT_TIMEOUT_MS


@pytest.mark.parametrize(
    ("timeout_ms", "expected"),
    [
        (60_000, {"options": "-c statement_timeout=60000"}),
        (1, {"options": "-c statement_timeout=1"}),
        (0, {}),
        (-1, {}),
    ],
)
def test_statement_timeout_connect_args(monkeypatch, timeout_ms, expected):
    monkeypatch.setattr(settings, "DB_STATEMENT_TIMEOUT_MS", timeout_ms)

    assert test_module._statement_timeout_connect_args() == expected
