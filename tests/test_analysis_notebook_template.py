import pytest

from app.db.model import AnalysisNotebookTemplate
from app.db.types import EntityType

from .utils import (
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "analysis-notebook-template"
ADMIN_ROUTE = "/admin/analysis-notebook-template"
MODEL = AnalysisNotebookTemplate


@pytest.fixture
def json_data(analysis_notebook_template_json_data):
    return analysis_notebook_template_json_data


@pytest.fixture
def model(analysis_notebook_template):
    return analysis_notebook_template


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
    assert data["scale"] == json_data["scale"]
    assert data["type"] == EntityType.analysis_notebook_template
    assert data["specifications"]["python"] == json_data["specifications"]["python"]
    assert len(data["specifications"]["inputs"]) == len(json_data["specifications"]["inputs"])
    assert (
        data["specifications"]["docker"]["image_repository"]
        == json_data["specifications"]["docker"]["image_repository"]
    )
    assert data["assignment_id"] == json_data["assignment_id"]
    assert "contributions" in data

    check_creation_fields(data)


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
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


def test_read_many_1(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_read_many_2(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_filter_by_assignment_id(client, json_data):
    assignment_a = "assignment-101"
    assignment_b = "physiology_basics"
    assignment_c = "no-such-assignment"

    id_a1 = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "a1", "assignment_id": assignment_a}
    ).json()["id"]
    id_a2 = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "a2", "assignment_id": assignment_a}
    ).json()["id"]
    id_b = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "b", "assignment_id": assignment_b}
    ).json()["id"]
    assert_request(client.post, url=ROUTE, json=json_data | {"name": "none", "assignment_id": None})

    data = assert_request(client.get, url=ROUTE, params={"assignment_id": assignment_a}).json()[
        "data"
    ]
    assert {d["id"] for d in data} == {id_a1, id_a2}

    data = assert_request(
        client.get, url=ROUTE, params={"assignment_id__in": [assignment_a, assignment_b]}
    ).json()["data"]
    assert {d["id"] for d in data} == {id_a1, id_a2, id_b}

    data = assert_request(
        client.get, url=ROUTE, params={"assignment_id__in": [assignment_c]}
    ).json()["data"]
    assert data == []

    data = assert_request(client.get, url=ROUTE, params={"lifecycle_status": "active"}).json()[
        "data"
    ]
    assert len(data) == 4


@pytest.mark.parametrize("assignment_id", ["", "x" * 256])
def test_assignment_id_invalid(client, json_data, assignment_id):
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"assignment_id": assignment_id},
        expected_status_code=422,
    )


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            AnalysisNotebookTemplate: 1,
        },
        expected_counts_after={
            AnalysisNotebookTemplate: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)
