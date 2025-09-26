from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from pydantic import TypeAdapter

from app.db.model import AnalysisNotebookExecution, Generation, Usage
from app.db.types import ActivityType

from .utils import (
    PROJECT_ID,
    assert_request,
    check_activity_create_one__unauthorized_entities,
    check_activity_update_one,
    check_activity_update_one__fail_if_generated_ids_exists,
    check_activity_update_one__fail_if_generated_ids_unauthorized,
    check_creation_fields,
    check_missing,
    check_pagination,
)

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "analysis-notebook-execution"
ADMIN_ROUTE = "/admin/analysis-notebook-execution"
CIRCUIT_ROUTE = "/circuit"
MODEL = AnalysisNotebookExecution


@pytest.fixture
def json_data(
    analysis_notebook_template,
    analysis_notebook_environment,
    analysis_notebook_result,
    circuit,
):
    return {
        "start_time": str(datetime.now(UTC)),
        "end_time": str(datetime.now(UTC)),
        "used_ids": [str(circuit.id)],
        "generated_ids": [str(analysis_notebook_result.id)],
        "analysis_notebook_template_id": str(analysis_notebook_template.id),
        "analysis_notebook_environment_id": str(analysis_notebook_environment.id),
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data, *, empty_ids: bool = False):
    assert "id" in data

    if empty_ids:
        assert data["used"] == []
        assert data["generated"] == []
    else:
        assert data["used"] == [
            {
                "id": json_data["used_ids"][0],
                "type": "circuit",
                "authorized_project_id": PROJECT_ID,
                "authorized_public": False,
            }
        ]
        assert data["generated"] == [
            {
                "id": json_data["generated_ids"][0],
                "type": "analysis_notebook_result",
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
    assert data["type"] == ActivityType.analysis_notebook_execution
    assert data["analysis_notebook_template"]["id"] == json_data["analysis_notebook_template_id"]
    assert (
        data["analysis_notebook_environment"]["id"] == json_data["analysis_notebook_environment_id"]
    )


def test_create_one(client, client_admin, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)


def test_create_one__empty_ids(client, client_admin, json_data):
    json_data = {k: v for k, v in json_data.items() if k not in {"used_ids", "generated_ids"}}

    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)


def test_create_one__unauthorized_entities(
    db,
    client_user_1,
    client_user_2,
    circuit_json_data,
    json_data,
):
    u1_private_entity = assert_request(
        client_user_1.post, url=CIRCUIT_ROUTE, json=circuit_json_data | {"authorized_public": False}
    ).json()["id"]
    u2_private_entity = assert_request(
        client_user_2.post, url=CIRCUIT_ROUTE, json=circuit_json_data | {"authorized_public": False}
    ).json()["id"]
    u2_public_entity = assert_request(
        client_user_2.post, url=CIRCUIT_ROUTE, json=circuit_json_data | {"authorized_public": True}
    ).json()["id"]
    check_activity_create_one__unauthorized_entities(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=u1_private_entity,
        u2_private_entity_id=u2_private_entity,
        u2_public_entity_id=u2_public_entity,
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(root_circuit, analysis_notebook_result, create_id):
    return [
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[],
        ),
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[str(analysis_notebook_result.id)],
        ),
        create_id(
            used_ids=[],
            generated_ids=[str(analysis_notebook_result.id)],
        ),
    ]


def test_filtering(client, models, root_circuit, analysis_notebook_result):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(client.get, url=ROUTE, params={"used__id": str(root_circuit.id)}).json()[
        "data"
    ]
    assert len(data) == 2

    data = assert_request(
        client.get, url=ROUTE, params={"generated__id": str(analysis_notebook_result.id)}
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "used__id": str(root_circuit.id),
            "generated__id": str(analysis_notebook_result.id),
        },
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"used__id__in": [str(root_circuit.id), str(analysis_notebook_result.id)]},
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generated__id__in": [str(root_circuit.id), str(analysis_notebook_result.id)]},
    ).json()["data"]
    assert len(data) == 2


def test_delete_one(db, client, models):
    # sanity check
    assert _count_associations(db, models[0]) == 1
    assert _count_associations(db, models[1]) == 2
    assert _count_associations(db, models[2]) == 1

    data = assert_request(client.delete, url=f"{ROUTE}/{models[1]}").json()
    assert data["id"] == str(models[1])
    assert _is_deleted(db, data["id"])

    assert _count_associations(db, models[0]) == 1
    assert _count_associations(db, models[1]) == 0
    assert _count_associations(db, models[2]) == 1

    data = assert_request(client.delete, url=f"{ROUTE}/{models[2]}").json()
    assert data["id"] == str(models[2])
    assert _is_deleted(db, data["id"])

    assert _count_associations(db, models[0]) == 1
    assert _count_associations(db, models[1]) == 0
    assert _count_associations(db, models[2]) == 0

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert {d["id"] for d in data} == {str(models[0])}


def _count_associations(db, activity_id):
    n_usages = db.execute(
        sa.select(sa.func.count(Usage.usage_activity_id)).where(
            Usage.usage_activity_id == activity_id
        )
    ).scalar()
    n_generations = db.execute(
        sa.select(sa.func.count(Generation.generation_activity_id)).where(
            Generation.generation_activity_id == activity_id
        )
    ).scalar()

    return n_usages + n_generations


def _is_deleted(db, model_id):
    return db.get(MODEL, model_id) is None


def test_update_one(client, client_admin, root_circuit, analysis_notebook_result, create_id):
    check_activity_update_one(
        client=client,
        client_admin=client_admin,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        used_id=root_circuit.id,
        generated_id=analysis_notebook_result.id,
        constructor_func=create_id,
    )


def test_update_one__fail_if_generated_ids_unauthorized(
    db, client_user_1, client_user_2, json_data, circuit_json_data
):
    """Test that it is not allowed to update generated_ids with unauthorized entities."""

    u1_private_entity = assert_request(
        client_user_1.post, url=CIRCUIT_ROUTE, json=circuit_json_data | {"authorized_public": False}
    ).json()["id"]
    u2_private_entity = assert_request(
        client_user_2.post, url=CIRCUIT_ROUTE, json=circuit_json_data | {"authorized_public": False}
    ).json()["id"]

    check_activity_update_one__fail_if_generated_ids_unauthorized(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=u1_private_entity,
        u2_private_entity_id=u2_private_entity,
    )


def test_update_one__fail_if_generated_ids_exists(
    client, root_circuit, analysis_notebook_result, create_id
):
    """Test activity Generation associations cannot be updated if they already exist."""
    check_activity_update_one__fail_if_generated_ids_exists(
        client=client,
        route=ROUTE,
        entity_id_1=root_circuit.id,
        entity_id_2=analysis_notebook_result.id,
        constructor_func=create_id,
    )
