import pytest

from app.db.model import TaskConfig
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    assert_request,
    check_authorization,
    check_entity_delete_one,
    check_entity_read_response,
    check_entity_update_one,
    check_entity_update_one__fail_if_nested_ids_exists,
    check_entity_update_one__fail_if_nested_ids_unauthorized,
    check_missing,
    check_pagination,
    create_cell_morphology_id,
)

ROUTE = "task-config"
ADMIN_ROUTE = "/admin/task-config"
TASK_CONFIG_TYPE = "skeletonization__config"


@pytest.fixture
def json_data(task_config_json_data):
    return task_config_json_data


@pytest.fixture
def public_json_data(json_data):
    return json_data | {"authorized_public": True}


@pytest.fixture
def create_id(client, task_config_with_parent_json_data):
    def _create_id(**kwargs):
        return assert_request(
            client.post,
            url=ROUTE,
            json=task_config_with_parent_json_data | kwargs,
        ).json()["id"]

    return _create_id


@pytest.fixture
def model_id(task_config_id):
    return task_config_id


def _assert_read_response(data, json_data):
    check_entity_read_response(data, json_data, EntityType.task_config)
    assert "input" in data
    assert "parent_id" in data
    assert data["scan_parameters"] == json_data["scan_parameters"]


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_create_one_with_parent(client, task_config_with_parent_json_data):
    json_data = task_config_with_parent_json_data
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert json_data["parent_id"] == task_config_with_parent_json_data["parent_id"]


def test_create_one_with_nested_relationships(
    client, task_config_with_nested_relationships_json_data
):
    json_data = task_config_with_nested_relationships_json_data
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    input_ids = json_data["input_ids"]
    assert data["input"] == [
        {
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "id": input_ids[0],
            "type": "em_cell_mesh",
        },
    ]


def test_read_one(clients, model_id, json_data):
    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(clients.user_1.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)

    data = assert_request(clients.admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            TaskConfig: 1,
        },
        expected_counts_after={
            TaskConfig: 0,
        },
    )


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


def test_update_one__fail_if_nested_ids_unauthorized(
    db, client_user_1, client_user_2, json_data, subject_id, brain_region_id
):
    """Test that it is not allowed to update the nested ids with unauthorized entities."""

    user2_generated_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    check_entity_update_one__fail_if_nested_ids_unauthorized(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u2_private_entity_id=user2_generated_id,
        relationship_key="input_ids",
    )


def test_update_one__fail_if_nested_ids_exists(
    db, client_user_1, json_data, subject_id, brain_region_id
):
    """Test that nested ids cannot be updated if they already exist."""
    user1_generated_id = create_cell_morphology_id(
        client_user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    check_entity_update_one__fail_if_nested_ids_exists(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=user1_generated_id,
        relationship_key="input_ids",
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(clients, public_json_data):
    check_authorization(ROUTE, clients.user_1, clients.user_2, clients.no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(create_id):
    return [create_id(name=f"config-{i}") for i in range(3)]


def test_filtering_ordering(client, models, public_campaign_id):
    def _req(query):
        # always filter by task_config_type to exclude the parent campaign
        return assert_request(
            client.get,
            url=ROUTE,
            params=query | {"task_config_type": TASK_CONFIG_TYPE},
        ).json()["data"]

    data = _req({})
    assert len(data) == len(models)

    data = _req({"name__ilike": "config"})
    assert len(data) == len(models)

    data = _req({"name": "config-0"})
    assert len(data) == 1
    assert data[0]["name"] == "config-0"

    data = _req({"parent_id": public_campaign_id})
    assert len(data) == len(models)

    data = _req({"parent_id__in": [public_campaign_id]})
    assert len(data) == len(models)

    data = _req({"order_by": "-name"})
    assert [d["name"] for d in data] == ["config-2", "config-1", "config-0"]

    data = _req({"order_by": "-name", "name__in": ["config-1", "config-2"]})
    assert [d["name"] for d in data] == ["config-2", "config-1"]

    data = _req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = _req({"ilike_search": "*description*"})
    assert len(data) == len(models)

    data = _req({"ilike_search": "config-1"})
    assert len(data) == 1
