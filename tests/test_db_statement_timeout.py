from http import HTTPStatus

import pytest
import sqlalchemy as sa
from psycopg.errors import AdminShutdown
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db.session import _statement_timeout_connect_args
from app.errors import ApiErrorCode

from tests import utils

ROUTE = "/brain-atlas"


def _raise_after_setting_timeout(*, db, **_):
    db.execute(sa.text("SET LOCAL statement_timeout = 50"))
    db.execute(sa.text("SELECT pg_sleep(5)"))


def _raise_operational_error(**_):
    statement = "SELECT 1"
    raise OperationalError(statement, {}, AdminShutdown())


def test_statement_timeout_is_set_on_connections(session_client):
    manager = session_client.app.state.database_session_manager
    with manager.engine.connect() as connection:
        value = connection.execute(
            sa.text("SELECT setting FROM pg_settings WHERE name = 'statement_timeout'")
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

    assert _statement_timeout_connect_args() == expected


def test_cancelled_query_returns_504(client_admin, monkeypatch):
    monkeypatch.setattr("app.queries.common.router_read_many", _raise_after_setting_timeout)

    response = utils.assert_request(
        client_admin.get, url=ROUTE, expected_status_code=HTTPStatus.GATEWAY_TIMEOUT
    )

    assert response.json()["error_code"] == ApiErrorCode.QUERY_TIMEOUT
    assert response.json()["details"] == {"statement_timeout_ms": settings.DB_STATEMENT_TIMEOUT_MS}


def test_other_operational_errors_are_not_handled(client_admin, monkeypatch):
    monkeypatch.setattr("app.queries.common.router_read_many", _raise_operational_error)

    with pytest.raises(OperationalError):
        client_admin.get(ROUTE)
