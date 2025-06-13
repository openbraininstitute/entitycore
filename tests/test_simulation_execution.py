from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter

from app.db.types import ActivityType

from .utils import PROJECT_ID, assert_request, check_creation_fields

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "simulation-execution"


@pytest.fixture
def json_data(morphology_id, emodel_id):
    return {
        "start_time": str(datetime.now(UTC)),
        "end_time": str(datetime.now(UTC)),
        "used_ids": [str(morphology_id)],
        "generated_ids": [str(emodel_id)],
        "status": "done",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["used"] == [
        {
            "id": json_data["used_ids"][0],
            "type": "reconstruction_morphology",
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
        }
    ]
    assert data["generated"] == [
        {
            "id": json_data["generated_ids"][0],
            "type": "emodel",
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
        }
    ]
    check_creation_fields(data)
    assert DateTimeAdapter.validate_python(data["start_time"]) == DateTimeAdapter.validate_python(
        json_data["start_time"]
    )
    assert DateTimeAdapter.validate_python(data["end_time"]) == DateTimeAdapter.validate_python(
        json_data["end_time"]
    )
    assert data["type"] == ActivityType.simulation_execution
    assert data["status"] == json_data["status"]


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)
