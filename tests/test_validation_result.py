import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.model import ValidationResult

from .utils import USER_SUB_ID_1, assert_request, check_entity_delete_one, check_entity_update_one

MODEL = ValidationResult
ROUTE = "/validation-result"
ADMIN_ROUTE = "/admin/validation-result"


@pytest.fixture
def json_data(morphology_id):
    return {
        "passed": True,
        "validated_entity_id": str(morphology_id),
        "name": "test_validation_result",
        "authorized_public": False,
    }


@pytest.fixture
def public_json_data(public_morphology_id):
    return {
        "passed": True,
        "validated_entity_id": str(public_morphology_id),
        "name": "test_validation_result",
        "authorized_public": True,
    }


@pytest.fixture
def create(client, json_data):
    def _create(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()

    return _create


@pytest.fixture
def model(create):
    return create()


def _assert_read_response(data, json_data):
    assert data["name"] == json_data["name"]
    assert data["passed"] == json_data["passed"]
    assert data["validated_entity_id"] == json_data["validated_entity_id"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["creation_date"] == data["update_date"]
    assert "assets" in data


def test_update_one(clients, public_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        patch_payload={
            "name": "name",
            "passed": False,
        },
        optional_payload=None,
    )


def test_read_one(client, client_admin, validation_result_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{validation_result_id}").json()
    _assert_read_response(data, json_data)
    assert data["id"] == validation_result_id

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{validation_result_id}").json()
    _assert_read_response(data, json_data)
    assert data["id"] == validation_result_id


def test_create_one(client: TestClient, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is False

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is False

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is False


def test_create_one__public(client, public_json_data):
    json_data = public_json_data
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is True

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is True

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)
    assert data["authorized_public"] is True


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            ValidationResult: 1,
        },
        expected_counts_after={
            ValidationResult: 0,
        },
    )


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


def test_filtering__one_entry(client, validation_result_id, morphology_id):
    # no results expected for unrelated id
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"validated_entity_id": str(validation_result_id)},
    ).json()["data"]

    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"validated_entity_id": str(morphology_id)},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["validated_entity_id"] == str(morphology_id)


@pytest.fixture
def models(create, morphology_id, emodel_id):
    return [
        create(
            name="m1",
            passed=True,
            validated_entity_id=str(morphology_id),
        ),
        create(
            name="m2",
            passed=False,
            validated_entity_id=str(morphology_id),
        ),
        create(
            name="e1",
            passed=True,
            validated_entity_id=str(emodel_id),
        ),
        create(
            name="e2",
            passed=False,
            validated_entity_id=str(emodel_id),
        ),
    ]


def test_filtering__many_entries(client, models, morphology_id, emodel_id):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"validated_entity_id": str(morphology_id)},
    ).json()["data"]

    assert len(data) == 2
    assert data[0]["validated_entity_id"] == models[0]["validated_entity_id"]
    assert data[1]["validated_entity_id"] == models[1]["validated_entity_id"]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"validated_entity_id": str(emodel_id)},
    ).json()["data"]

    assert len(data) == 2
    assert data[0]["validated_entity_id"] == models[2]["validated_entity_id"]
    assert data[1]["validated_entity_id"] == models[3]["validated_entity_id"]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1},
    ).json()["data"]
    assert len(data) == len(models)
