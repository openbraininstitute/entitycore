import pytest

from app.db.model import Publication

from .utils import (
    add_db,
    assert_request,
    check_missing,
)

ROUTE = "/publication"


@pytest.fixture
def json_data(publication_json_data):
    return publication_json_data


def _assert_read_response(data, json_data):
    assert data["DOI"] == json_data["DOI"]
    assert data["title"] == json_data["title"]
    assert data["authors"] == json_data["authors"]
    assert data["publication_year"] == json_data["publication_year"]
    assert data["abstract"] == json_data["abstract"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]


@pytest.fixture
def create_id(client_admin, json_data):
    def _create_id(**kwargs):
        return assert_request(client_admin.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(publication):
    return publication.id


def test_create_one(client_admin, json_data):
    data = assert_request(client_admin.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, models):  # noqa: ARG001
    data = assert_request(client.get, url=ROUTE, params={"page_size": 2}).json()
    assert "facets" in data
    assert "data" in data
    assert data["facets"] is None
    assert len(data["data"]) == 2


@pytest.fixture
def models(db, json_data, person_id):
    res = []
    for i in range(5):
        row = add_db(
            db,
            Publication(
                **json_data
                | {
                    "title": f"t{i}",
                    "DOI": f"doi-{i}",
                    "publication_year": 2020 + i,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
            ),
        )
        res.append(row)

    return res


def test_filtering_sorting(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"publication_year__gte": 2020})
    assert len(data) == len(models)

    data = req({"publication_year__in": [2021, 2024]})
    assert {d["publication_year"] for d in data} == {2021, 2024}

    data = req({"publication_year__in": [2021, 2024], "order_by": "publication_year"})
    assert [d["publication_year"] for d in data] == [2021, 2024]

    data = req({"publication_year__in": [2021, 2024], "order_by": "-publication_year"})
    assert [d["publication_year"] for d in data] == [2024, 2021]

    data = req({"publication_year__lte": 2022, "order_by": "title"})
    assert [d["publication_year"] for d in data] == [2020, 2021, 2022]

    data = req({"publication_year__lte": 2022, "order_by": "-title"})
    assert [d["publication_year"] for d in data] == [2022, 2021, 2020]
