import pytest

from app.db.model import GenericResult
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_read_many,
    check_missing,
    check_pagination,
)

ROUTE = "generic-result"
ADMIN_ROUTE = "/admin/generic-result"


@pytest.fixture
def json_data(generic_result_json_data):
    return generic_result_json_data | {"result_type": "validation_type"}


@pytest.fixture
def public_json_data(public_generic_result_json_data):
    return public_generic_result_json_data | {"result_type": "validation_type"}


@pytest.fixture
def model(generic_result):
    if hasattr(generic_result, "result_type") and generic_result.result_type is None:
        generic_result.result_type = "validation_type"
    return generic_result


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
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["type"] == EntityType.generic_result

    check_creation_fields(data)


def test_user_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert not data["authorized_public"]
    assert data["authorized_project_id"] == PROJECT_ID


def test_user_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many_1(client, model, json_data):
    check_entity_read_many(ROUTE, client, model, lambda d: _assert_read_response(d, json_data))


def test_user_update_one(client, model, json_data):
    update_data = {"name": "new-name"}
    data = assert_request(client.put, url=f"{ROUTE}/{model.id}", json=update_data).json()
    _assert_read_response(data, json_data | update_data)


def test_user_delete_one(client, db, model):
    check_entity_delete_one(
        ROUTE,
        client,
        db,
        model,
        expected_counts_before={
            GenericResult: 1,
        },
        expected_counts_after={
            GenericResult: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    objs = [
        GenericResult(
            **json_data
            | {
                "name": f"s-{i}",
                "result_type": "validation_type",
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        )
        for i in range(3)
    ]
    return add_all_db(db, objs)


def test_filtering(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    assert models is not None

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == 3

    data = req({"name__like": "s-%"})
    assert len(data) == 3

    data = req({"name": "s-0"})
    assert len(data) == 1
    assert data[0]["name"] == "s-0"

    data = req({"name": "s-none"})
    assert len(data) == 0
