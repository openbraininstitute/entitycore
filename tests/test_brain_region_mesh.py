import pytest

from .utils import (
    assert_request,
    check_authorization,
    check_missing,
    check_pagination,
)

ROUTE = "/brain-region-mesh"


@pytest.fixture
def json_data(
    brain_region_id,
):
    return {
        "brain_region_id": str(brain_region_id),
        "description": "my-description",
        "name": "my-name",
        "authorized_public": False,
    }


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["type"] == "mesh"


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    json_data,
):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_filtering(client, brain_region_id, brain_region_hierarchy_id, model_id):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"brain_region__id": str(model_id)},
    ).json()["data"]

    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"brain_region__id": str(brain_region_id)},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["brain_region"]["id"] == str(brain_region_id)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "brain_region__name": "RedRegion",
            "brain_region__hierarchy_id": str(brain_region_hierarchy_id),
        },
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["brain_region"]["id"] == str(brain_region_id)
