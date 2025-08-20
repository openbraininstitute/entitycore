from unittest.mock import ANY

import pytest

from app.db.model import ExternalUrl
from app.db.types import EXTERNAL_SOURCE_INFO, ExternalSource

from .utils import (
    add_db,
    assert_request,
    check_missing,
)

ROUTE = "/external-url"


@pytest.fixture
def json_data(external_url_json_data):
    return external_url_json_data


def _assert_read_response(data, json_data):
    expected = {
        "id": ANY,
        "creation_date": ANY,
        "update_date": ANY,
        "created_by": ANY,
        "updated_by": ANY,
    } | json_data
    assert data == expected


@pytest.fixture
def create_id(client_admin, json_data):
    def _create_id(**kwargs):
        return assert_request(client_admin.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(external_url):
    return str(external_url.id)


def test_create_one(client_admin, json_data):
    data = assert_request(client_admin.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_create_one__url_validation(client_admin, json_data):
    # should not allow registering a external_url without a url
    data = assert_request(
        client_admin.post,
        url=ROUTE,
        json={k: v for k, v in json_data.items() if k != "url"},
        expected_status_code=422,
    ).json()
    assert data["message"] == "Validation error"

    valid_urls = [
        "https://channelpedia.epfl.ch/wikipages/1",
        "https://channelpedia.epfl.ch/wikipages/2?a=1&b=2",
        "https://channelpedia.epfl.ch/wikipages/3#section",
    ]

    for url in valid_urls:
        data = assert_request(client_admin.post, url=ROUTE, json=json_data | {"url": url}).json()
        assert data["url"] == url

    invalid_urls = [
        "channelpedia.epfl.ch/wikipages/1",  # missing scheme
        "https://example.com/wikipages/1",  # invalid domain
        "ftp://channelpedia.epfl.ch",  # invalid scheme
        "/",
        "",
    ]

    for url in invalid_urls:
        data = assert_request(
            client_admin.post, url=ROUTE, json=json_data | {"url": url}, expected_status_code=422
        ).json()
        assert data["message"] == "Validation error"

    # duplicate should not be registered
    url = "https://channelpedia.epfl.ch/wikipages/1"
    data = assert_request(
        client_admin.post, url=ROUTE, json=json_data | {"url": url}, expected_status_code=409
    ).json()
    assert data["error_code"] == "ENTITY_DUPLICATED"


def test_read_one(client, model_id, json_data):
    expected = json_data | {"id": model_id}

    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, expected)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], expected)


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, models):  # noqa: ARG001
    data = assert_request(client.get, url=ROUTE, params={"page_size": 2}).json()
    assert "facets" in data
    assert "data" in data
    assert data["facets"] is None
    assert len(data["data"]) == 2


@pytest.fixture
def models(db, person_id):
    data = [
        {
            "source": ExternalSource.channelpedia,
            "url": f"{EXTERNAL_SOURCE_INFO[ExternalSource.channelpedia]['allowed_url']}/wiki",
        },
        {
            "source": ExternalSource.icgenealogy,
            "url": f"{EXTERNAL_SOURCE_INFO[ExternalSource.icgenealogy]['allowed_url']}/wiki",
        },
        {
            "source": ExternalSource.modeldb,
            "url": f"{EXTERNAL_SOURCE_INFO[ExternalSource.modeldb]['allowed_url']}/wiki",
        },
        {
            "source": ExternalSource.channelpedia,
            "url": f"{EXTERNAL_SOURCE_INFO[ExternalSource.channelpedia]['allowed_url']}/wiki",
        },
    ]
    res = []
    for i, d in enumerate(data):
        row = add_db(
            db,
            ExternalUrl(
                **d
                | {
                    "name": f"name-{i}",
                    "description": f"description-{i}",
                    "url": f"{d['url']}/page-{i}",
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
            ),
        )
        res.append(row)

    return res


def test_filtering_sorting(client, models, person_id):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"created_by__id": person_id})
    assert len(data) == len(models)

    data = req({"source": "channelpedia"})
    assert len(data) == 2
    assert {d["name"] for d in data} == {"name-0", "name-3"}

    data = req({"name": "name-1"})
    assert len(data) == 1
    assert {d["name"] for d in data} == {"name-1"}

    data = req({"source": "channelpedia", "order_by": "name"})
    assert [d["name"] for d in data] == ["name-0", "name-3"]

    data = req({"source": "channelpedia", "order_by": "-name"})
    assert [d["name"] for d in data] == ["name-3", "name-0"]
