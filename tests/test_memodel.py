import itertools as it

import pytest

from .utils import BEARER_TOKEN, PROJECT_HEADERS, create_reconstruction_morphology_id, add_db
from app.db.model import EModel

ROUTE = "/memodel"


@pytest.mark.usefixtures("skip_project_check")
def test_create_emodel(db, client, species_id, strain_id, brain_region_id):
    mmodel_id = create_reconstruction_morphology_id(
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        authorized_public=False,
    )

    emodel_id = (
        add_db(
            db,
            EModel(
                name="Test EModel",
                species_id=species_id,
                strain_id=strain_id,
                brain_region_id=brain_region_id,
                exemplar_morphology_id=mmodel_id,
            ),
        )
    ).id

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test EModel Description",
            "name": "Test EModel Name",
            "legacy_id": "Test Legacy ID",
            "iteration": "test iteration",
            "score": -1,
            "seed": -1,
            "exemplar_morphology_id": exemplar_morphology_id,
        },
    )
    assert response.status_code == 200, f"Failed to create emodel: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, f"Failed to get id for emodel: {data}"
    assert data["species"]["id"] == species_id, f"Failed to get species_id for emodel: {data}"
    assert data["strain"]["id"] == strain_id, f"Failed to get strain_id for emodel: {data}"

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, f"Failed to get emodels: {response.text}"
