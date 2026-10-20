import gzip
import sys

import pytest
from fastapi.testclient import TestClient

from app.application import create_app
from app.config import settings
from app.logger import L

from tests import test_brain_region, utils

if sys.version_info >= (3, 14):
    from compression.zstd import decompress as zstd_decompress
else:
    from zstandard import decompress as zstd_decompress

ROUTE = "/brain-region-hierarchy"
HEADERS = utils.AUTH_HEADER_USER_1 | utils.PROJECT_HEADERS
DECOMPRESS = {
    "zstd": zstd_decompress,
    "gzip": gzip.decompress,
    None: lambda body: body,
}


def _get_raw(client, url, accept_encoding, headers=None):
    """Return the response and its body as sent on the wire, without client-side decoding."""
    headers = HEADERS | {"Accept-Encoding": accept_encoding} | (headers or {})
    with client.stream("GET", url, headers=headers) as response:
        body = b"".join(response.iter_raw())
    return response, body


@pytest.fixture
def hierarchy_url(db, brain_region_hierarchy_id):
    utils.add_brain_region_hierarchy(db, test_brain_region.HIERARCHY, brain_region_hierarchy_id)
    return f"{ROUTE}/{brain_region_hierarchy_id}/hierarchy"


@pytest.fixture
def expected_body(client, hierarchy_url):
    response = client.get(hierarchy_url, headers={"Accept-Encoding": "identity"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    return response.content


@pytest.mark.parametrize(
    ("accept_encoding", "expected_encoding"),
    [
        ("zstd", "zstd"),
        ("gzip", "gzip"),
        ("gzip, deflate, br, zstd", "zstd"),
        ("gzip, br", "gzip"),
        ("zstd;q=0, gzip", "gzip"),
        ("br", None),
        ("identity", None),
        ("deflate", None),
    ],
)
def test_compression(
    client_no_auth, hierarchy_url, expected_body, accept_encoding, expected_encoding
):
    response, body = _get_raw(client_no_auth, hierarchy_url, accept_encoding)

    assert response.status_code == 200
    assert response.headers.get("content-encoding") == expected_encoding
    assert "Accept-Encoding" in response.headers["vary"]
    assert int(response.headers["content-length"]) == len(body)
    assert DECOMPRESS[expected_encoding](body) == expected_body
    if expected_encoding:
        assert len(body) < len(expected_body)


def test_small_response_not_compressed(client_no_auth):
    response, body = _get_raw(client_no_auth, "/health", "gzip, br, zstd")

    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert int(response.headers["content-length"]) == len(body)


def test_cached_hierarchy_response_not_mutated(client_no_auth, hierarchy_url, expected_body):
    """The cached hierarchy must not keep headers set by the middlewares in previous requests."""
    for accept_encoding, expected_encoding in [
        ("zstd", "zstd"),
        ("identity", None),
        ("gzip", "gzip"),
        ("zstd", "zstd"),
    ]:
        response, body = _get_raw(
            client_no_auth,
            hierarchy_url,
            accept_encoding,
            headers={"Origin": "https://example.org"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == expected_encoding
        assert response.headers["vary"].count("Origin") == 1
        assert response.headers["vary"].count("Accept-Encoding") == 1
        assert DECOMPRESS[expected_encoding](body) == expected_body


def test_access_log_reports_compressed_size(client_no_auth, hierarchy_url):
    records = []
    handler_id = L.add(lambda message: records.append(message.record), level="INFO")
    try:
        _, body = _get_raw(client_no_auth, hierarchy_url, "zstd")
    finally:
        L.remove(handler_id)

    [extra] = [r["extra"] for r in records if r["message"] == "request_completed"]
    assert extra["content_encoding"] == "zstd"
    assert extra["response_size"] == len(body)


@pytest.mark.parametrize(("enabled", "expected_encoding"), [(True, "zstd"), (False, None)])
def test_compression_enabled_setting(monkeypatch, enabled, expected_encoding):
    monkeypatch.setattr(settings, "COMPRESSION_ENABLED", enabled)
    # openapi.json is large enough to be compressed, and it doesn't need the lifespan
    client = TestClient(create_app())
    response, body = _get_raw(client, "/openapi.json", "zstd")

    assert response.status_code == 200
    assert response.headers.get("content-encoding") == expected_encoding
    assert DECOMPRESS[expected_encoding](body).startswith(b'{"openapi":')
