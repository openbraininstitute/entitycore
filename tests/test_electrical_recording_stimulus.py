import pytest

from app.db.model import (
    ElectricalRecordingStimulus,
)
from app.db.types import EntityType

from .utils import (
    assert_request,
    check_authorization,
    check_missing,
    check_pagination,
)

ROUTE = "/electrical-recording-stimulus"
MODEL_CLASS = ElectricalRecordingStimulus
TYPE = EntityType.electrical_recording_stimulus.value


@pytest.fixture
def json_data(trace_id_minimal):
    return {
        "name": "my-stimulus",
        "description": "my-stimulus-description",
        "dt": 0.1,
        "injection_type": "current_clamp",
        "shape": "sinusoidal",
        "start_time": None,
        "end_time": None,
        "recording_id": str(trace_id_minimal),
    }


def _assert_read_response(data, json_data):
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["type"] == TYPE
    assert data["created_by"]["id"] == data["updated_by"]["id"]


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
    assert data["id"] == str(model_id)


def test_read_many(client, model_id, json_data):
    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)
    assert data["data"][0]["id"] == str(model_id)


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
