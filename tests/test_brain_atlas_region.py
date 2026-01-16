import pytest

from app.db.model import BrainAtlasRegion

from .utils import (
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "brain-atlas-region"
ADMIN_ROUTE = "/admin/brain-atlas-region"
MODEL = BrainAtlasRegion


@pytest.fixture
def json_data(brain_atlas_id, brain_region_id):
    return {
        "brain_atlas_id": str(brain_atlas_id),
        "brain_region_id": str(brain_region_id),
        "volume": 10,
        "is_leaf_region": False,
    }


@pytest.fixture
def model(db, json_data, person_id):
    return add_db(
        db,
        MODEL(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": str(PROJECT_ID),
            },
        ),
    )


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["brain_atlas_id"] == json_data["brain_atlas_id"]
    assert data["volume"] == json_data["volume"]
    assert data["is_leaf_region"] == json_data["is_leaf_region"]

    check_creation_fields(data)


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "volume": 100,
            "is_leaf_region": True,
        },
        optional_payload=None,
    )


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_user_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = assert_request(client_admin.get, url=f"/admin/{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            MODEL: 1,
        },
        expected_counts_after={
            MODEL: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)
