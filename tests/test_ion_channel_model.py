import itertools as it
import uuid

from fastapi.testclient import TestClient

from app.db.types import EntityType
from app.schemas.ion_channel_model import IonChannelModelRead

from tests.routers.test_asset import _upload_entity_asset

ROUTE = "/ion-channel-model"


def create(
    client: TestClient,
    species_id: str,
    strain_id: str,
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
            "species_id": species_id,
            "strain_id": strain_id,
            "authorized_public": authorized_public,
        },
    )

    return response


def test_create(client: TestClient, species_id: str, strain_id: str, brain_region_id: uuid.UUID):
    response = create(client, species_id, strain_id, brain_region_id)
    assert response.status_code == 200, f"Failed to create icm: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == str(brain_region_id), f"Failed to get id for icm: {data}"
    assert data["species"]["id"] == species_id, f"Failed to get species_id for icm: {data}"
    assert data["strain"]["id"] == strain_id, f"Failed to get strain_id for icm: {data}"

    response = client.get(ROUTE)
    assert response.status_code == 200, f"Failed to get icms: {response.text}"


def test_read_one(client: TestClient, species_id: str, strain_id: str, brain_region_id: uuid.UUID):
    icm_res = create(client, species_id, strain_id, brain_region_id)
    icm: dict = icm_res.json()
    icm_id = icm.get("id")
    _upload_entity_asset(client, EntityType.ion_channel_model, uuid.UUID(icm_id))

    response = client.get(f"{ROUTE}/{icm_id}")

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


def test_read_many(client: TestClient, species_id: str, strain_id: str, brain_region_id: uuid.UUID):
    count = 11
    icm_res = [create(client, species_id, strain_id, brain_region_id) for _ in range(count)]

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

    IonChannelModelRead.model_validate(icm_res[0].json())


def test_sorted(client: TestClient, species_id: str, strain_id: str, brain_region_id: uuid.UUID):
    count = 11
    icm_res = [create(client, species_id, strain_id, brain_region_id) for _ in range(count)]

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
    species_id: str,
    strain_id: str,
    brain_region_id: uuid.UUID,
):
    public_obj = create(
        client_user_1, species_id, strain_id, brain_region_id, name="public", authorized_public=True
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    inaccessible_obj = create(
        client_user_2, species_id, strain_id, brain_region_id, name="inaccessible_obj"
    )

    assert inaccessible_obj.status_code == 200

    inaccessible_obj = inaccessible_obj.json()

    private_obj = create(
        client_user_1,
        species_id,
        strain_id,
        brain_region_id,
        name="private",
        authorized_public=False,
    )
    assert private_obj.status_code == 200
    private_obj = private_obj.json()

    private_obj1 = create(
        client_user_1,
        species_id,
        strain_id,
        brain_region_id,
        name="private1",
        authorized_public=False,
    )
    assert private_obj1.status_code == 200
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = client_user_1.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj["id"],
        private_obj1["id"],
    }

    response = client_user_1.get(f"{ROUTE}/{inaccessible_obj['id']}")
    assert response.status_code == 404

    # only return public results
    response = client_no_project.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == public_obj["id"]


def test_paginate(client: TestClient, species_id: str, strain_id: str, brain_region_id: uuid.UUID):
    total_items = 29
    _icm_res = [
        create(client, species_id, strain_id, brain_region_id, name=str(i))
        for i in range(total_items)
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
