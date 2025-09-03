import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.model import MEModelCalibrationResult

from .utils import assert_request, count_db_class

MODEL = MEModelCalibrationResult
ROUTE = "/memodel-calibration-result"
ADMIN_ROUTE = "/admin/memodel-calibration-result"


@pytest.fixture
def json_data(memodel_id):
    return {
        "calibrated_entity_id": str(memodel_id),
        "authorized_public": False,
        "threshold_current": 0.8,
        "holding_current": 0.2,
        "rin": 100.0,  # Optional field, can be None
    }


@pytest.fixture
def create(client, json_data):
    def _create(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()

    return _create


def _assert_read_response(data, json_data):
    assert data["threshold_current"] == json_data["threshold_current"]
    assert data["holding_current"] == json_data["holding_current"]
    assert data["rin"] == json_data.get("rin")
    assert data["calibrated_entity_id"] == json_data["calibrated_entity_id"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["creation_date"] == data["update_date"]
    assert data["authorized_public"] is json_data["authorized_public"]


def test_read_one(client: TestClient, memodel_calibration_result_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{memodel_calibration_result_id}").json()
    _assert_read_response(data, json_data)
    assert data["id"] == memodel_calibration_result_id


def test_create_one(client: TestClient, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)


def test_delete_one(db, client, client_admin, memodel_calibration_result_id):
    model_id = memodel_calibration_result_id

    assert count_db_class(db, MEModelCalibrationResult) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, MEModelCalibrationResult) == 0


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


def test_filtering__one_entry(client, memodel_calibration_result_id, memodel_id, morphology_id):
    # no results expected for unrelated id
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(morphology_id)},
    ).json()["data"]

    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(memodel_id)},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["calibrated_entity_id"] == str(memodel_id)
    assert data[0]["id"] == str(memodel_calibration_result_id)


def test_memodel_relationship(client, memodel_id, memodel_calibration_result_id):
    data = assert_request(client.get, url=f"memodel/{memodel_id}").json()
    assert data["calibration_result"]["id"] == str(memodel_calibration_result_id)
    assert data["calibration_result"]["calibrated_entity_id"] == str(memodel_id)


@pytest.fixture
def models(create, memodel_id):
    return [
        create(
            threshold_current=0.5,
            holding_current=0.1,
            calibrated_entity_id=str(memodel_id),
        ),
        create(
            threshold_current=0.5,
            holding_current=0.1,
            calibrated_entity_id=str(memodel_id),
        ),
    ]


def test_filtering__many_entries(client, models, memodel_id):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"calibrated_entity_id": str(memodel_id)},
    ).json()["data"]

    assert len(data) == 2
    assert data[0]["calibrated_entity_id"] == models[0]["calibrated_entity_id"]
    assert data[1]["calibrated_entity_id"] == models[1]["calibrated_entity_id"]
