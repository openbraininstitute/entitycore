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


@pytest.fixture(scope="session")
def test_error_endpoint() -> str:
    """Fixture to add a test endpoint that raises an unhandled error.

    Use the session scope because the endpoint isn't removed until the end of the tests.
    """
    path = "/test-error-endpoint"

    @app.get(path)
    def test_endpoint():
        L.info("test message")
        msg = "test error"
        raise RuntimeError(msg)

    return path


def _filter_logs(logs, keys=("message", "extra")):
    return [{k: rec[k] for k in keys} for rec in logs]


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
            "message": "request_completed",
            "extra": {
                "user_id": ADMIN_SUB_ID,
                "request_id": ANY,
                "serialized": ANY,
                # only in the final log:
                "method": "GET",
                "url": f"http://testserver{endpoint}",
                "route_template": endpoint,
                "status_code": 200,
                "status_class": 2,
                "process_time_ms": ANY,
                "response_size": ANY,
                "client": "testclient",
                "forwarded_for": "127.1.2.3",
                "user_agent": "testclient",
            },
        },
    ]
    assert _filter_logs(logs) == expected


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
            "message": "request_completed",
            "extra": {
                "request_id": ANY,
                "serialized": ANY,
                # only in the final log:
                "method": "GET",
                "url": f"http://testserver{endpoint}",
                "route_template": endpoint,
                "status_code": 200,
                "status_class": 2,
                "process_time_ms": ANY,
                "response_size": ANY,
                "client": "testclient",
                "forwarded_for": "127.1.2.3",
                "user_agent": "testclient",
            },
        },
    ]
    assert _filter_logs(logs) == expected


def test_error_request_context(logs, client_no_auth, test_error_endpoint):
    """Test that the request context middleware handles errors."""
    client = client_no_auth
    endpoint = test_error_endpoint
    headers = {"x-forwarded-for": "127.1.2.3"}
    with pytest.raises(RuntimeError, match="test error"):
        client.get(endpoint, headers=headers)

    expected = [
        {
            "message": "test message",
            "extra": {
                "request_id": ANY,
                "serialized": ANY,
            },
        },
        {
            "message": "request_failed",
            "extra": {
                "request_id": ANY,
                "serialized": ANY,
                # only in the final log:
                "method": "GET",
                "url": f"http://testserver{endpoint}",
                "status_code": 500,
                "status_class": 5,
                "process_time_ms": ANY,
                "client": "testclient",
                "forwarded_for": "127.1.2.3",
                "user_agent": "testclient",
            },
        },
    ]
    assert _filter_logs(logs) == expected
