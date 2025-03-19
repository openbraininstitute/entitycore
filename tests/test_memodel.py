import uuid
import itertools as it

import pytest
from fastapi.testclient import TestClient
# from .conftest import CreateIds

from .utils import BEARER_TOKEN, PROJECT_HEADERS, create_reconstruction_morphology_id, add_db
from app.db.model import EModel

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
