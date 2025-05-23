import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.model import CalibrationResult

from .utils import assert_request

MODEL = CalibrationResult
ROUTE = "/calibration-result"


@pytest.fixture
def json_data(memodel_id):
    return {
        "value": 0.0654321,
        "calibrated_entity_id": str(memodel_id),
        "name": "threshold_current",
        "description": "threshold_current (mV) of the memodel for testing",
        "authorized_public": False,
    }


@pytest.fixture
def create(client, json_data):
    def _create(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()

    return _create


def _assert_read_response(data, json_data):
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["value"] == json_data["value"]
    assert data["calibrated_entity_id"] == json_data["calibrated_entity_id"]
    assert data["createdBy"]["id"] == data["updatedBy"]["id"]
    assert data["creation_date"] == data["update_date"]


def test_read_one(client: TestClient, calibrated_result_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{calibrated_result_id}").json()
    _assert_read_response(data, json_data)
    assert data["id"] == calibrated_result_id


def test_create_one(client: TestClient, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


def test_filtering__one_entry(client, calibration_result_id, memodel_id):
    # no results expected for unrelated id
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(calibration_result_id)},
    ).json()["data"]

    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(memodel_id)},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["calibrated_entity_id"] == str(memodel_id)


@pytest.fixture
def models(create, memodel_id, emodel_id):
    return [
        create(
            name="me1",
            description="test memodel 1",
            value=0.1234567,
            validated_entity_id=str(memodel_id),
        ),
        create(
            name="me2",
            description="test memodel 2",
            value=0.0,
            validated_entity_id=str(memodel_id),
        ),
        create(
            name="e1",
            description="test emodel 1",
            value=0.1234567,
            validated_entity_id=str(emodel_id),
        ),
        create(
            name="e2",
            description="test emodel 2",
            value=0.0,
            validated_entity_id=str(emodel_id),
        ),
    ]


def test_filtering__many_entries(client, models, memodel_id, emodel_id):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(memodel_id)},
    ).json()["data"]

    assert len(data) == 2
    assert data[0]["calibrated_entity_id"] == models[0]["calibrated_entity_id"]
    assert data[1]["calibrated_entity_id"] == models[1]["calibrated_entity_id"]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(emodel_id)},
    ).json()["data"]

    assert len(data) == 2
    assert data[0]["calibrated_entity_id"] == models[2]["calibrated_entity_id"]
    assert data[1]["calibrated_entity_id"] == models[3]["calibrated_entity_id"]
