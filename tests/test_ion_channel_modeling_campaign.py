import pytest

from app.db.model import IonChannelModelingCampaign, IonChannelModelingConfig
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_entity_delete_one,
    check_entity_read_response,
    check_missing,
    check_pagination,
)

ROUTE = "ion-channel-modeling-campaign"
ADMIN_ROUTE = "/admin/ion-channel-modeling-campaign"
MODEL = IonChannelModelingCampaign


@pytest.fixture
def json_data(ion_channel_modeling_campaign_json_data):
    return ion_channel_modeling_campaign_json_data


@pytest.fixture
def public_json_data(json_data):
    return json_data | {"authorized_public": True}


@pytest.fixture
def model_id(ion_channel_modeling_campaign_id):
    return ion_channel_modeling_campaign_id


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    check_entity_read_response(data, json_data, EntityType.ion_channel_modeling_campaign)
    assert "input_recordings" in data
    assert "ion_channel_modeling_configs" in data
    assert data["scan_parameters"] == json_data["scan_parameters"]


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


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
            IonChannelModelingCampaign: 1,
        },
        expected_counts_after={
            IonChannelModelingCampaign: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(clients, public_json_data):
    check_authorization(ROUTE, clients.user_1, clients.user_2, clients.no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    db_campaigns = add_all_db(
        db,
        [
            MODEL(
                **(
                    json_data
                    | {
                        "name": f"campaign-{i}",
                        "description": f"campaign-description-{i}",
                        "scan_parameters": {"foo": "bar"},
                        "created_by_id": person_id,
                        "updated_by_id": person_id,
                        "authorized_project_id": PROJECT_ID,
                    }
                )
            )
            for i in range(4)
        ],
    )

    mapping = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
    ]

    for i, campaign in enumerate(db_campaigns):
        for j in mapping[i]:
            add_db(
                db,
                IonChannelModelingConfig(
                    name=f"config-{j}",
                    description=f"config-{j}",
                    ion_channel_modeling_campaign_id=campaign.id,
                    scan_parameters=campaign.scan_parameters,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                    authorized_project_id=PROJECT_ID,
                ),
            )

    return db_campaigns


def test_filtering_ordering(client, models):
    def _req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = _req({})
    assert len(data) == len(models)

    data = _req({"name__ilike": "campaign"})
    assert len(data) == len(models)

    data = _req({"name": "campaign-1"})
    assert len(data) == 1
    assert data[0]["name"] == "campaign-1"

    data = _req({"ion_channel_modeling_config__name": "config-2"})
    assert {d["name"] for d in data} == {"campaign-1", "campaign-2"}

    data = _req({"order_by": "-name"})
    assert [d["name"] for d in data] == [f"campaign-{i}" for i in range(4)][::-1]

    data = _req({"ion_channel_modeling_config__name": "config-2", "order_by": "name"})
    assert [d["name"] for d in data] == ["campaign-1", "campaign-2"]

    data = _req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = _req({"ilike_search": "*description*"})
    assert len(data) == len(models)

    data = _req({"ilike_search": "campaign-2"})
    assert len(data) == 1
