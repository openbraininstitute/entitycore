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
ADMIN_ROUTE = "/admin/electrical-recording-stimulus"
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


def test_update_one(client, model_id):
    new_name = "my_new_stimulus_name"
    new_description = "my_new_stimulus_description"

    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model_id}",
        json={
            "name": new_name,
            "description": new_description,
        },
    ).json()

    assert data["name"] == new_name
    assert data["description"] == new_description

    # Test setting and unsetting optional fields
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model_id}",
        json={
            "dt": 0.2,
            "start_time": 1.0,
            "end_time": 5.0,
        },
    ).json()
    assert data["dt"] == 0.2
    assert data["start_time"] == 1.0
    assert data["end_time"] == 5.0

    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model_id}",
        json={
            "start_time": None,
            "end_time": None,
        },
    ).json()
    assert data["start_time"] is None
    assert data["end_time"] is None


def test_update_one__public(client, json_data):
    # make private entity public
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data
        | {
            "authorized_public": True,
        },
    ).json()

    # should not be allowed to update it once public
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{data['id']}",
        json={"name": "foo"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"


def test_user_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)
    assert data["id"] == str(model_id)


def test_admin_read_one(client_admin, model_id, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
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
