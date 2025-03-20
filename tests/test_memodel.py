import operator as op
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.model import EModel

from .conftest import CreateIds, MEModels
from .utils import BEARER_TOKEN, PROJECT_HEADERS, add_db, create_reconstruction_morphology_id

ROUTE = "/memodel"


@pytest.mark.usefixtures("skip_project_check")
def test_get_memodel(client: TestClient, memodel_id):
    response = client.get(f"{ROUTE}/{memodel_id}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memodel_id
    assert "mmodel" in data
    assert "emodel" in data
    assert "brain_region" in data
    assert "species" in data
    assert "strain" in data
    assert "mtypes" in data
    assert "etypes" in data


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_create_memodel(
    client: TestClient,
    species_id: str,
    strain_id: str,
    brain_region_id: int,
    morphology_id: str,
    emodel_id: str,
):
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test MEModel Description",
            "name": "Test MEModel Name",
            "mmodel_id": morphology_id,
            "emodel_id": emodel_id,
        },
    )
    assert response.status_code == 200, f"Failed to create memodel: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, f"Failed to get id for memodel: {data}"
    assert data["species"]["id"] == species_id, f"Failed to get species_id for memodel: {data}"
    assert data["strain"]["id"] == strain_id, f"Failed to get strain_id for memodel: {data}"

    response = client.get(f"{ROUTE}/{data['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, f"Failed to get mmodels: {response.text}"


@pytest.mark.usefixtures("skip_project_check")
def test_facets(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]

    assert facets == {
        "mtype": [],
        "etype": [],
        "strain": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 8,
                "type": "species",
            },
            {
                "id": ids.species_ids[1],
                "label": "TestSpecies1",
                "count": 8,
                "type": "species",
            },
        ],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_agent_1",
                "count": 16,
                "type": "agent",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_agent_2",
                "count": 16,
                "type": "agent",
            },
        ],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 8, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 8, "type": "brain_region"},
        ],
        "mmodel": [
            {
                "id": ids.mmodel_ids[0],
                "label": "test mmodel 0",
                "count": 8,
                "type": "mmodel",
            },
            {
                "id": ids.mmodel_ids[1],
                "label": "test mmodel 1",
                "count": 8,
                "type": "mmodel",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 8,
                "type": "emodel",
            },
            {
                "id": ids.emodel_ids[1],
                "label": "1",
                "count": 8,
                "type": "emodel",
            },
        ],
    }


@pytest.mark.usefixtures("skip_project_check")
def test_filtered_facets(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={
            "species__id": ids.species_ids[0],
            "emodel__name__ilike": "%0%",
            "with_facets": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 4,
                "type": "species",
            }
        ],
        "strain": [],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_agent_1",
                "count": 4,
                "type": "agent",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_agent_2",
                "count": 4,
                "type": "agent",
            },
        ],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 2, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 2, "type": "brain_region"},
        ],
        "mmodel": [
            {
                "id": ids.mmodel_ids[0],
                "label": "test mmodel 0",
                "count": 2,
                "type": "mmodel",
            },
            {
                "id": ids.mmodel_ids[1],
                "label": "test mmodel 1",
                "count": 2,
                "type": "mmodel",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 4,
                "type": "emodel",
            }
        ],
    }


@pytest.mark.usefixtures("skip_project_check")
def test_facets_with_search(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"search": "foo", "with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 8,
                "type": "species",
            }
        ],
        "strain": [],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_agent_1",
                "count": 8,
                "type": "agent",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_agent_2",
                "count": 8,
                "type": "agent",
            },
        ],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 4, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 4, "type": "brain_region"},
        ],
        "mmodel": [
            {
                "id": ids.mmodel_ids[0],
                "label": "test mmodel 0",
                "count": 4,
                "type": "mmodel",
            },
            {
                "id": ids.mmodel_ids[1],
                "label": "test mmodel 1",
                "count": 4,
                "type": "mmodel",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 4,
                "type": "emodel",
            },
            {
                "id": ids.emodel_ids[1],
                "label": "1",
                "count": 4,
                "type": "emodel",
            },
        ],
    }


@pytest.mark.usefixtures("skip_project_check")
def test_pagination(client, create_memodel_ids: CreateIds):
    total_items = 29
    create_memodel_ids(total_items)

    response = client.get(
        ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": total_items + 1}
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 1):
        expected_items = i
        response = client.get(
            ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": expected_items}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == expected_items

        assert [int(d["name"]) for d in data] == list(
            range(total_items - 1, total_items - expected_items - 1, -1)
        )

    items = []
    for i in range(1, total_items + 1):
        response = client.get(
            ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page": i, "page_size": 1}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    data_ids = [int(i["name"]) for i in items]
    assert list(reversed(data_ids)) == list(range(total_items))


@pytest.mark.usefixtures("skip_project_check")
def test_query_memodel(client: TestClient, create_memodel_ids: CreateIds):
    count = 11
    create_memodel_ids(count)

    response = client.get(
        ROUTE,
        params={"page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11
    assert data == sorted(data, key=op.itemgetter("creation_date"), reverse=True)


@pytest.mark.usefixtures("skip_project_check")
def test_sorted(client: TestClient, create_memodel_ids: CreateIds):
    count = 10
    create_memodel_ids(count)

    response = client.get(
        ROUTE,
        params={"order_by": "-name"},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()["data"]

    assert data == sorted(data, key=op.itemgetter("name"), reverse=True)


@pytest.mark.usefixtures("skip_project_check")
def test_filter_memodel(client: TestClient, faceted_memodels: MEModels):
    mmodels = faceted_memodels

    response = client.get(
        ROUTE,
        params={
            "species__id": mmodels.species_ids[0],
            "emodel__name__ilike": "%0%",
        },
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["facets"] is None
    assert "data" in response_json

    data = response_json["data"]

    assert all(d["species"]["id"] == mmodels.species_ids[0] for d in data)
    assert all(d["emodel"]["name"] == "0" for d in data)


@pytest.mark.usefixtures("skip_project_check")
def test_memodel_search(client: TestClient, faceted_memodels: MEModels):  # noqa: ARG001
    response = client.get(
        ROUTE,
        params={"search": "foo"},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["facets"] is None
    assert "data" in response_json

    data = response_json["data"]

    assert all(d["description"] == "foo" for d in data)


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(
    db: Session, client, species_id, strain_id, brain_region_id, morphology_id, emodel_id
):
    emodel_json = {
        "brain_region_id": brain_region_id,
        "description": "description",
        "legacy_id": "Test Legacy ID",
        "name": "Test name",
        "species_id": species_id,
        "strain_id": strain_id,
        "emodel_id": emodel_id,
        "mmodel_id": morphology_id,
    }

    public_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "public obj",
            "authorized_public": True,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    unauthorized_relations = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json,
    )

    assert unauthorized_relations.status_code == 403

    mmodel_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        authorized_public=False,
    )

    unauthorized_emodel = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json | {"mmodel_id": mmodel_id},
    )

    assert unauthorized_emodel.status_code == 403

    emodel_id = str(
        add_db(
            db,
            EModel(
                authorized_public=False,
                brain_region_id=brain_region_id,
                species_id=species_id,
                exemplar_morphology_id=mmodel_id,
                authorized_project_id="42424242-4242-4000-9000-424242424242",
            ),
        ).id
    )

    inaccessible_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json | {"mmodel_id": mmodel_id, "emodel_id": emodel_id},
    )

    assert inaccessible_obj.status_code == 200

    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json | {"name": "private obj 0"},
    )
    assert private_obj0.status_code == 200
    private_obj0 = private_obj0.json()

    private_obj1 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "private obj 1",
        },
    )
    assert private_obj1.status_code == 200
    private_obj1 = private_obj1.json()

    public_obj_diff_project = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json
        | {
            "mmodel_id": mmodel_id,
            "emodel_id": emodel_id,
            "authorized_public": True,
        },
    )

    assert public_obj_diff_project.status_code == 200

    public_obj_diff_project = public_obj_diff_project.json()

    # only return results that matches the desired project, and public ones
    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    data = response.json()["data"]
    assert len(data) == 4

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj0["id"],
        private_obj1["id"],
        public_obj_diff_project["id"],
    }

    response = client.get(
        f"{ROUTE}/{inaccessible_obj['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS
    )

    assert response.status_code == 404
