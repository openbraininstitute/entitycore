from unittest.mock import ANY

import pytest

from app.db.model import IonChannel

from .utils import (
    add_db,
    assert_request,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
    check_missing,
)

ROUTE = "/ion-channel"
ADMIN_ROUTE = "/admin/ion-channel"


@pytest.fixture
def json_data(ion_channel_json_data):
    return ion_channel_json_data


def _assert_read_response(actual, expected):
    assert actual == expected | {
        "id": ANY,
        "created_by": ANY,
        "updated_by": ANY,
        "creation_date": ANY,
        "update_date": ANY,
    }


@pytest.fixture
def create_id(client_admin, json_data):
    def _create_id(**kwargs):
        return assert_request(client_admin.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(ion_channel):
    return ion_channel.id


def test_create_one(client_admin, json_data):
    data = assert_request(client_admin.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(clients, json_data):
    check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
    )


def test_update_one(clients, json_data):
    check_global_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "my-ion-channel",
            "description": "my-description",
            "label": "my-label",
            "gene": "my-gene",
            "synonyms": ["a", "b", "c"],
        },
    )


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            IonChannel: 1,
        },
        expected_counts_after={
            IonChannel: 0,
        },
    )


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
            IonChannel(
                **json_data
                | {
                    "name": f"name-{i}",
                    "label": f"label-{i}",
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

    data = req({"name__ilike": "name-"})
    assert len(data) == len(models)

    data = req({"name__in": ["name-0", "name-2"]})
    assert {d["name"] for d in data} == {"name-0", "name-2"}

    data = req({"search": "name", "order_by": "-name"})
    assert [d["name"] for d in data] == [
        "name-4",
        "name-3",
        "name-2",
        "name-1",
        "name-0",
    ]

    data = req({"ilike_search": "description"})
    assert len(data) == len(models)

    data = req({"ilike_search": "name-1"})
    assert len(data) == 1
