from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter

from app.db.types import ActivityType

from .utils import (
    PROJECT_ID,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
)

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "simulation-generation"


@pytest.fixture
def json_data(morphology_id, emodel_id):
    return {
        "start_time": str(datetime.now(UTC)),
        "end_time": str(datetime.now(UTC)),
        "used_ids": [str(morphology_id)],
        "generated_ids": [str(emodel_id)],
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data, *, empty_ids=False):
    assert "id" in data

    if empty_ids:
        assert len(data["used"]) == 0
        assert len(data["generated"]) == 0
    else:
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
    assert data["type"] == ActivityType.simulation_generation.value


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)


def test_create_one__empty_ids(client, json_data):
    json_data = {k: v for k, v in json_data.items() if k not in {"used_ids", "generated_ids"}}

    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data, empty_ids=True)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(morphology_id, root_circuit, simulation_result, create_id):
    return [
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[],
        ),
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[str(root_circuit.id)],
        ),
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[str(simulation_result.id)],
        ),
        create_id(
            used_ids=[str(root_circuit.id), str(simulation_result.id)],
            generated_ids=[str(root_circuit.id), str(simulation_result.id)],
        ),
        create_id(
            used_ids=[str(morphology_id), str(root_circuit.id)],
            generated_ids=[str(simulation_result.id)],
        ),
    ]


def test_filtering(client, models, root_circuit):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(client.get, url=ROUTE, params={"used__id": str(root_circuit.id)}).json()[
        "data"
    ]
    assert len(data) == 5

    data = assert_request(
        client.get, url=ROUTE, params={"generated__id": str(root_circuit.id)}
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"used__id": str(root_circuit.id), "generated__id": str(root_circuit.id)},
    ).json()["data"]
    assert len(data) == 2
