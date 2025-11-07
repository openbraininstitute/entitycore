from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter

from app.db.model import (
    Generation,
    SkeletonizationCampaign,
    SkeletonizationConfig,
    SkeletonizationConfigGeneration,
    Usage,
)
from app.db.types import ActivityType

from .utils import (
    PROJECT_ID,
    assert_request,
    check_activity_create_one__unauthorized_entities,
    check_activity_delete_one,
    check_activity_update_one,
    check_activity_update_one__fail_if_generated_ids_exists,
    check_activity_update_one__fail_if_generated_ids_unauthorized,
    check_creation_fields,
    check_missing,
    check_pagination,
    create_skeletonization_campaign_id,
    create_skeletonization_config_id,
)

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "skeletonization-config-generation"
ADMIN_ROUTE = "/admin/skeletonization-config-generation"


@pytest.fixture
def json_data(skeletonization_campaign_id, skeletonization_config_id):
    return {
        "start_time": str(datetime.now(UTC)),
        "end_time": str(datetime.now(UTC)),
        "used_ids": [skeletonization_campaign_id],
        "generated_ids": [skeletonization_config_id],
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


def _assert_read_response(data, json_data, *, empty_ids=False):
    assert "id" in data

    if empty_ids:
        assert len(data["used"]) == 0
        assert len(data["generated"]) == 0
    else:
        assert data["used"] == [
            {
                "id": json_data["used_ids"][0],
                "type": "skeletonization_campaign",
                "authorized_project_id": PROJECT_ID,
                "authorized_public": False,
            }
        ]
        assert data["generated"] == [
            {
                "id": json_data["generated_ids"][0],
                "type": "skeletonization_config",
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
    assert data["type"] == ActivityType.skeletonization_config_generation.value


def test_create_one(clients, json_data):
    data = assert_request(clients.user_1.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(clients, json_data, model_id):
    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(clients.user_1.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)

    data = assert_request(clients.admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
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


def test_create_one__unauthorized_entities(db, client_user_1, client_user_2, json_data):
    """Do not allow associations with entities that are not authorized to the user."""

    user1_private_used_id = create_skeletonization_campaign_id(
        client_user_1,
        authorized_public=False,
    )
    user2_private_used_id = create_skeletonization_campaign_id(
        client_user_2,
        authorized_public=False,
    )
    user2_public_used_id = create_skeletonization_campaign_id(
        client_user_2,
        authorized_public=True,
    )
    check_activity_create_one__unauthorized_entities(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=user1_private_used_id,
        u2_private_entity_id=user2_private_used_id,
        u2_public_entity_id=user2_public_used_id,
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def skeletonization_config_id_1(client, skeletonization_campaign_id, em_cell_mesh):
    return create_skeletonization_config_id(
        client=client,
        skeletonization_campaign_id=skeletonization_campaign_id,
        em_cell_mesh_id=em_cell_mesh.id,
    )


@pytest.fixture
def skeletonization_config_id_2(client, skeletonization_campaign_id, em_cell_mesh):
    return create_skeletonization_config_id(
        client=client,
        skeletonization_campaign_id=skeletonization_campaign_id,
        em_cell_mesh_id=em_cell_mesh.id,
    )


@pytest.fixture
def models(
    create_id,
    skeletonization_campaign_id,
    skeletonization_config_id_1,
    skeletonization_config_id_2,
):
    return [
        create_id(
            used_ids=[skeletonization_campaign_id],
            generated_ids=[],
        ),
        create_id(
            used_ids=[skeletonization_campaign_id],
            generated_ids=[skeletonization_config_id_1],
        ),
        create_id(
            used_ids=[skeletonization_campaign_id],
            generated_ids=[
                skeletonization_config_id_1,
                skeletonization_config_id_2,
            ],
        ),
        create_id(
            used_ids=[],
            generated_ids=[],
        ),
    ]


def test_filtering(
    client,
    models,
    skeletonization_campaign_id,
    skeletonization_config_id_1,
    skeletonization_config_id_2,
):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get, url=ROUTE, params={"used__id": skeletonization_campaign_id}
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        client.get, url=ROUTE, params={"generated__id": skeletonization_config_id_1}
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "used__id": skeletonization_campaign_id,
            "generated__id": skeletonization_config_id_2,
        },
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"used__id__in": [skeletonization_campaign_id]},
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generated__id__in": [skeletonization_config_id_2]},
    ).json()["data"]
    assert len(data) == 1


def test_delete_one(db, clients, json_data):
    check_activity_delete_one(
        db=db,
        clients=clients,
        json_data=json_data,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        expected_counts_before={
            SkeletonizationCampaign: 2,
            SkeletonizationConfig: 1,
            Usage: 1,
            Generation: 1,
            SkeletonizationConfigGeneration: 1,
        },
        expected_counts_after={
            SkeletonizationCampaign: 2,
            SkeletonizationConfig: 1,
            Usage: 0,
            Generation: 0,
            SkeletonizationConfigGeneration: 0,
        },
    )


def test_update_one(
    client,
    client_admin,
    skeletonization_campaign_id,
    skeletonization_config_id,
    create_id,
):
    check_activity_update_one(
        client=client,
        client_admin=client_admin,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        used_id=skeletonization_campaign_id,
        generated_id=skeletonization_config_id,
        constructor_func=create_id,
    )


def test_update_one__fail_if_generated_ids_unauthorized(
    db, client_user_1, client_user_2, json_data
):
    """Test that it is not allowed to update generated_ids with unauthorized entities."""

    user1_private_used_id = create_skeletonization_campaign_id(
        client_user_1,
        authorized_public=False,
    )
    user2_private_used_id = create_skeletonization_campaign_id(
        client_user_2,
        authorized_public=False,
    )
    check_activity_update_one__fail_if_generated_ids_unauthorized(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=user1_private_used_id,
        u2_private_entity_id=user2_private_used_id,
    )


def test_update_one__fail_if_generated_ids_exists(
    client, skeletonization_campaign_id, skeletonization_config_id, create_id
):
    """Test activity Generation associations cannot be updated if they already exist."""
    check_activity_update_one__fail_if_generated_ids_exists(
        client=client,
        route=ROUTE,
        entity_id_1=skeletonization_campaign_id,
        entity_id_2=skeletonization_config_id,
        constructor_func=create_id,
    )
