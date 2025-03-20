import uuid
import itertools as it

import pytest
from fastapi.testclient import TestClient
from .conftest import MEModelIds

from .utils import BEARER_TOKEN, PROJECT_HEADERS, create_reconstruction_morphology_id, add_db
# from app.db.model import EModel


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
def test_facets(client: TestClient, faceted_memodel_ids: MEModelIds):
    ids = faceted_memodel_ids

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
def test_filtered_facets(client: TestClient, faceted_memodel_ids: MEModelIds):
    ids = faceted_memodel_ids

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
def test_facets_with_search(client: TestClient, faceted_memodel_ids: MEModelIds):
    ids = faceted_memodel_ids

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
