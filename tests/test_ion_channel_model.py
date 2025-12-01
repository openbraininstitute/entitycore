import itertools as it
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.model import IonChannelModel
from app.db.types import EntityType
from app.schemas.ion_channel_model import IonChannelModelRead

from .utils import (
    PROJECT_ID,
    TEST_DATA_DIR,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_update_one,
    upload_entity_asset,
)

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
ROUTE = "/ion-channel-model"
ADMIN_ROUTE = "/admin/ion-channel-model"


@pytest.fixture
def json_data(
    subject_id,
    brain_region_id,
):
    return {
        "description": "Test ICM Description",
        "name": "test_icm",
        "nmodl_suffix": "test_icm",
        "temperature_celsius": 0,
        "neuron_block": {},
        "brain_region_id": str(brain_region_id),
        "subject_id": subject_id,
        "authorized_public": False,
    }


def create(
    client: TestClient,
    subject_id: str,
    brain_region_id: uuid.UUID,
    name: str = "Test name",
    *,
    authorized_public=False,
):
    response = client.post(
        ROUTE,
        json={
            "description": "Test ICM Description",
            "name": name,
            "nmodl_suffix": name,
            "temperature_celsius": 0,
            "neuron_block": {},
            "brain_region_id": str(brain_region_id),
            "subject_id": subject_id,
            "authorized_public": authorized_public,
        },
    )

    return response


@pytest.fixture
def model_id(client, subject_id, brain_region_id):
    response = create(client, subject_id, brain_region_id)
    assert response.status_code == 200, f"Failed to create icm: {response.text}"
    return response.json()["id"]


def test_create(client: TestClient, subject_id: str, brain_region_id: uuid.UUID):
    response = create(client, subject_id, brain_region_id)
    assert response.status_code == 200, f"Failed to create icm: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == str(brain_region_id), f"Failed to get id for icm: {data}"
    assert data["subject"]["id"] == subject_id, f"Failed to get subject_id for icm: {data}"

    response = client.get(ROUTE)
    assert response.status_code == 200, f"Failed to get icms: {response.text}"


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
            "temperature_celsius": 25,
            "is_ljp_corrected": True,
        },
        optional_payload={
            "contact_email": "foo.bar@zee.com",
            "notice_text": "Notice text example",
        },
    )


def test_user_read_one(client, client_admin, subject_id: str, brain_region_id: uuid.UUID):
    icm_res = create(client, subject_id, brain_region_id)
    icm: dict = icm_res.json()
    icm_id = icm.get("id")
    with FILE_EXAMPLE_PATH.open("rb") as f:
        upload_entity_asset(
            client,
            EntityType.ion_channel_model,
            uuid.UUID(icm_id),
            files={"file": ("c.mod", f, "application/mod")},
            label="neuron_mechanisms",
        )

    response = client.get(f"{ROUTE}/{icm_id}")

    assert response.status_code == 200
    json = response.json()
    IonChannelModelRead.model_validate(json)
    assert json["id"] == icm_id
    assert len(json["assets"]) == 1

    response = client_admin.get(f"{ADMIN_ROUTE}/{icm_id}")

    assert response.status_code == 200
    json = response.json()
    IonChannelModelRead.model_validate(json)
    assert json["id"] == icm_id
    assert len(json["assets"]) == 1


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


def test_read_many(client: TestClient, subject_id: str, brain_region_id: uuid.UUID):
    count = 11
    icm_res = [create(client, subject_id, brain_region_id) for _ in range(count)]
    for icm in icm_res:
        with FILE_EXAMPLE_PATH.open("rb") as f:
            upload_entity_asset(
                client,
                EntityType.ion_channel_model,
                uuid.UUID(icm.json().get("id")),
                files={"file": ("c.mod", f, "application/mod")},
                label="neuron_mechanisms",
            )

    response = client.get(ROUTE, params={"page_size": 10})
    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(ROUTE, params={"page_size": 100})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11
    for single_data in data:
        assert len(single_data["assets"]) == 1

    IonChannelModelRead.model_validate(icm_res[0].json())


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            IonChannelModel: 1,
        },
        expected_counts_after={
            IonChannelModel: 0,
        },
    )


def test_sorted(client: TestClient, subject_id: str, brain_region_id: uuid.UUID):
    count = 11
    icm_res = [create(client, subject_id, brain_region_id) for _ in range(count)]

    response = client.get(ROUTE, params={"order_by": "+creation_date", "page_size": 100})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(ROUTE, params={"order_by": "-creation_date"})
    assert response.status_code == 200
    data = response.json()["data"]

    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(ROUTE, params={"order_by": "+creation_date", "page": 1, "page_size": 3})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3

    assert [row["id"] for row in data] == [str(res.json()["id"]) for res in icm_res][:3]


def test_authorization(
    client_user_1: TestClient,
    client_user_2: TestClient,
    client_no_project: TestClient,
    subject_id: str,
    brain_region_id: str,
):
    json_data = {
        "description": "Test description",
        "nmodl_suffix": "test",
        "temperature_celsius": 0,
        "neuron_block": {},
        "brain_region_id": brain_region_id,
        "subject_id": subject_id,
    }
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_paginate(client: TestClient, subject_id: str, brain_region_id: uuid.UUID):
    total_items = 29
    _icm_res = [
        create(client, subject_id, brain_region_id, name=str(i)) for i in range(total_items)
    ]
    response = client.get(ROUTE, params={"page_size": total_items + 1})

    assert response.status_code == 200
    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 1):
        expected_items = i
        response = client.get(ROUTE, params={"page_size": expected_items})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == expected_items

        assert [int(d["name"]) for d in data] == list(
            range(total_items - 1, total_items - expected_items - 1, -1)
        )

    items = []
    for i in range(1, total_items + 1):
        response = client.get(ROUTE, params={"page": i, "page_size": 1})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    data_ids = [int(i["name"]) for i in items]
    assert list(reversed(data_ids)) == list(range(total_items))


def test_brain_region_filter(db, client, brain_region_hierarchy_id, subject_id, person_id):
    def create_model_function(_db, name, brain_region_id):
        return IonChannelModel(
            name=name,
            description="Test ICM Description",
            nmodl_suffix=name,
            temperature_celsius=0,
            neuron_block={},
            brain_region_id=brain_region_id,
            subject_id=subject_id,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


@pytest.fixture
def ion_channel_models(db, json_data, person_id):
    return add_all_db(
        db,
        [
            IonChannelModel(
                **json_data
                | {
                    "name": "icm-0",
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "authorized_project_id": PROJECT_ID,
                }
            ),
            IonChannelModel(
                **json_data
                | {
                    "name": "icm-1",
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "authorized_project_id": PROJECT_ID,
                }
            ),
            IonChannelModel(
                **json_data
                | {
                    "name": "icm-2",
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "authorized_project_id": PROJECT_ID,
                    "temperature_celsius": None,
                }
            ),
        ],
    )


def test_filtering(client, ion_channel_models, person_id):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({})
    assert len(data) == len(ion_channel_models)

    data = req({"name": "icm-0", "with_facets": True})
    assert len(data) == 1

    data = req({"created_by__id": str(person_id), "with_facets": True})
    assert len(data) == len(ion_channel_models)

    data = req({"temperature_celsius": 0, "with_facets": True})
    assert len(data) == 2

    data = req({"temperature_celsius__lte": 1, "with_facets": True})
    assert len(data) == 2

    data = req({"temperature_celsius__gte": 1, "with_facets": True})
    assert len(data) == 0

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(ion_channel_models)
