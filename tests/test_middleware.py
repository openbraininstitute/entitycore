from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import ANY

import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.dependencies.auth import user_verified
from app.logger import L
from app.middleware import RequestContextMiddleware

from tests.utils import ADMIN_SUB_ID, AUTH_HEADER_ADMIN


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[dict]:
    http_client = httpx.Client()
    try:
        yield {"http_client": http_client}
    finally:
        http_client.close()  # ruff:ignore[blocking-http-call-httpx-in-async-function]


def _make_test_app() -> FastAPI:
    test_app = FastAPI(lifespan=_lifespan)
    test_app.add_middleware(RequestContextMiddleware)

    @test_app.get("/test-authenticated-endpoint", dependencies=[Depends(user_verified)])
    def authenticated_endpoint():
        L.info("test message")
        return {"ok": True}

    @test_app.get("/test-public-endpoint")
    def public_endpoint():
        L.info("test message")
        return {"ok": True}

    @test_app.get("/test-error-endpoint")
    def error_endpoint():
        L.info("test message")
        msg = "test error"
        raise RuntimeError(msg)

    return test_app


@pytest.fixture
def _test_client(_override_check_user_info):
    with TestClient(_make_test_app(), raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def client_no_auth(_test_client):
    return _test_client


@pytest.fixture
def client_admin(_test_client):
    return _test_client


@pytest.fixture
def logs():
    logs = []

    def capture_sink(message):
        logs.append(message.record)

    handler_id = L.add(capture_sink, level="INFO")
    yield logs
    L.remove(handler_id)


def _filter_logs(logs, keys=("message", "extra")):
    return [{k: rec[k] for k in keys} for rec in logs]


def test_authenticated_request_context(logs, client_admin):
    endpoint = "/test-authenticated-endpoint"
    headers = {"x-forwarded-for": "127.1.2.3"}
    result = client_admin.get(endpoint, headers=AUTH_HEADER_ADMIN | headers)

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


def test_public_request_context(logs, client_no_auth):
    endpoint = "/test-public-endpoint"
    headers = {"x-forwarded-for": "127.1.2.3"}
    result = client_no_auth.get(endpoint, headers=headers)

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


def test_error_request_context(logs, client_no_auth):
    endpoint = "/test-error-endpoint"
    headers = {"x-forwarded-for": "127.1.2.3"}
    result = client_no_auth.get(endpoint, headers=headers)

    assert result.status_code == 500

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
