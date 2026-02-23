from unittest.mock import ANY

import pytest
from fastapi import Depends

from app.application import app
from app.dependencies.auth import user_verified
from app.logger import L

from tests.utils import ADMIN_SUB_ID


@pytest.fixture
def logs():
    """Fixture to capture logs."""
    logs = []

    def capture_sink(message):
        logs.append(message.record)

    handler_id = L.add(capture_sink, level="INFO")
    yield logs
    L.remove(handler_id)


@pytest.fixture(scope="session")
def test_authenticated_endpoint() -> str:
    """Fixture to add an authenticated test endpoint to the app.

    Use the session scope because the endpoint isn't removed until the end of the tests.
    """
    path = "/test-authenticated-endpoint"

    @app.get(path, dependencies=[Depends(user_verified)])
    def test_endpoint():
        L.info("test message")
        return {"ok": True}

    return path


@pytest.fixture(scope="session")
def test_public_endpoint() -> str:
    """Fixture to add a public test endpoint to the app.

    Use the session scope because the endpoint isn't removed until the end of the tests.
    """
    path = "/test-public-endpoint"

    @app.get(path)
    def test_endpoint():
        L.info("test message")
        return {"ok": True}

    return path


def test_authenticated_request_context(logs, client_admin, test_authenticated_endpoint):
    """Test that the request context middleware adds user_id and request_id to logs."""
    client = client_admin
    endpoint = test_authenticated_endpoint
    headers = {"x-forwarded-for": "127.1.2.3"}
    result = client.get(test_authenticated_endpoint, headers=headers)

    assert result.status_code == 200

    expected = [
        {
            "message": "test message",
            "extra": {
                "request_id": ANY,
                "user_id": ADMIN_SUB_ID,
                "serialized": ANY,
            },
        },
        {
            "message": f"GET http://testserver{endpoint}",
            "extra": {
                "request_id": ANY,
                "user_id": ADMIN_SUB_ID,
                "forwarded_for": "127.1.2.3",
                "process_time": ANY,
                "status_code": 200,
                "client": "testclient",
                "serialized": ANY,
            },
        },
    ]
    assert [{k: rec[k] for k in ["message", "extra"]} for rec in logs] == expected


def test_public_request_context(logs, client_no_auth, test_public_endpoint):
    """Test that the request context middleware adds request_id to logs."""
    client = client_no_auth
    endpoint = test_public_endpoint
    headers = {"x-forwarded-for": "127.1.2.3"}
    result = client.get(endpoint, headers=headers)

    assert result.status_code == 200

    expected = [
        {
            "message": "test message",
            "extra": {
                "request_id": ANY,
                "serialized": ANY,
            },
        },
        {
            "message": f"GET http://testserver{endpoint}",
            "extra": {
                "request_id": ANY,
                "forwarded_for": "127.1.2.3",
                "process_time": ANY,
                "status_code": 200,
                "client": "testclient",
                "serialized": ANY,
            },
        },
    ]
    assert [{k: rec[k] for k in ["message", "extra"]} for rec in logs] == expected
