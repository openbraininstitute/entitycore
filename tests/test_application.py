from http import HTTPStatus

import pytest
import sqlalchemy as sa
from psycopg.errors import AdminShutdown
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.errors import ApiErrorCode
from app.schemas.types import HeaderKey

from tests import utils

BRAIN_ATLAS_ROUTE = "/brain-atlas"


def _raise_after_setting_timeout(*, db, **_):
    db.execute(sa.text("SET LOCAL statement_timeout = 50"))
    db.execute(sa.text("SELECT pg_sleep(5)"))


def _raise_operational_error(**_):
    statement = "SELECT 1"
    raise OperationalError(statement, {}, AdminShutdown())


def test_add_request_id_header(client_no_auth):
    response = client_no_auth.get("/health")
    assert response.status_code == 200
    assert HeaderKey.request_id in response.headers


def test_add_process_time_header(client_no_auth):
    response = client_no_auth.get("/health")
    assert response.status_code == 200
    assert HeaderKey.process_time in response.headers
    assert float(response.headers[HeaderKey.process_time]) >= 0


def test_query_timeout_returns_504(client_admin, monkeypatch):
    monkeypatch.setattr("app.queries.common.router_read_many", _raise_after_setting_timeout)

    response = utils.assert_request(
        client_admin.get, url=BRAIN_ATLAS_ROUTE, expected_status_code=HTTPStatus.GATEWAY_TIMEOUT
    )

    assert response.json()["error_code"] == ApiErrorCode.QUERY_TIMEOUT
    assert response.json()["details"] == {"statement_timeout_ms": settings.DB_STATEMENT_TIMEOUT_MS}


def test_other_operational_errors_are_not_handled(client_admin, monkeypatch):
    monkeypatch.setattr("app.queries.common.router_read_many", _raise_operational_error)

    with pytest.raises(OperationalError):
        client_admin.get(BRAIN_ATLAS_ROUTE)
