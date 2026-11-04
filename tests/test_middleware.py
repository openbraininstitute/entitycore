import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import ANY

import httpx2
import pytest
from fastapi import Depends, FastAPI
from fastapi.responses import Response, StreamingResponse
from fastapi.testclient import TestClient

from app.dependencies.auth import user_verified
from app.logger import L
from app.middleware import RequestContextMiddleware
from app.schemas.types import HeaderKey

from tests.utils import ADMIN_SUB_ID, AUTH_HEADER_ADMIN

SHARED_RESPONSE = Response(b"ok", media_type="text/plain", headers={HeaderKey.request_id: "app"})
SLOW_STREAM_DELAY = 0.2


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncGenerator[dict]:
    http_client = httpx2.Client()
    try:
        yield {"http_client": http_client}
    finally:
        http_client.close()


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

    @test_app.get("/test-shared-response-endpoint")
    def shared_response_endpoint():
        return SHARED_RESPONSE

    @test_app.get("/test-slow-stream-endpoint")
    def slow_stream_endpoint():
        async def body():
            yield b"first"
            await asyncio.sleep(SLOW_STREAM_DELAY)
            yield b"second"

        return StreamingResponse(body(), media_type="text/plain")

    @test_app.get("/test-stream-error-endpoint")
    def stream_error_endpoint():
        async def body():
            yield b"first"
            msg = "test stream error"
            raise RuntimeError(msg)

        return StreamingResponse(body(), media_type="text/plain")

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
                "content_encoding": None,
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
                "content_encoding": None,
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
                "route_template": endpoint,
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


def _completed_logs(logs):
    return [rec["extra"] for rec in logs if rec["message"] == "request_completed"]


def test_shared_response_headers_not_mutated(logs, client_no_auth):
    raw_headers_before = list(SHARED_RESPONSE.raw_headers)
    request_ids = []
    for _ in range(2):
        result = client_no_auth.get("/test-shared-response-endpoint")
        assert result.status_code == 200
        assert len(result.headers.get_list(HeaderKey.request_id)) == 1
        assert len(result.headers.get_list(HeaderKey.process_time)) == 1
        request_ids.append(result.headers[HeaderKey.request_id])

    assert SHARED_RESPONSE.raw_headers == raw_headers_before
    assert request_ids == [rec["request_id"] for rec in _completed_logs(logs)]
    assert len(set(request_ids)) == 2


def test_timings(logs, client_no_auth):
    result = client_no_auth.get("/test-slow-stream-endpoint")

    assert result.status_code == 200
    assert result.content == b"firstsecond"
    [extra] = _completed_logs(logs)
    assert extra["process_time_ms"] == round(float(result.headers[HeaderKey.process_time]) * 1000)
    # measured when the headers are sent, before streaming the body
    assert extra["process_time_ms"] < SLOW_STREAM_DELAY * 1000
    assert extra["response_size"] is None  # streaming response without content-length


def test_stream_error_request_context(logs, client_no_auth):
    endpoint = "/test-stream-error-endpoint"
    result = client_no_auth.get(endpoint)

    # the headers have already been sent when the error happens
    assert result.status_code == 200

    expected = [
        {
            "message": "request_failed",
            "extra": {
                "request_id": ANY,
                "serialized": ANY,
                "method": "GET",
                "url": f"http://testserver{endpoint}",
                "route_template": endpoint,
                "status_code": 200,
                "status_class": 2,
                "process_time_ms": ANY,
                "client": "testclient",
                "forwarded_for": "",
                "user_agent": "testclient",
            },
        },
    ]
    assert _filter_logs(logs) == expected
