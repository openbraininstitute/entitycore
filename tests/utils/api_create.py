from app.db.model import CellMorphologyProtocol, EModel, MEModel
from app.db.types import CellMorphologyGenerationType

from tests.utils import ROUTES


def create_cell_morphology_protocol_id(
    client,
    *,
    authorized_public: bool = False,
):
    response = client.post(
        ROUTES[CellMorphologyProtocol],
        json={
            "generation_type": CellMorphologyGenerationType.placeholder,
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def create_emodel_id(
    client,
    *,
    species_id,
    strain_id,
    brain_region_id,
    morphology_id,
    name="Test EModel Name",
    description="Test EModel Description",
    authorized_public: bool = False,
):
    response = client.post(
        ROUTES[EModel],
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id),
            "species_id": str(species_id),
            "strain_id": str(strain_id),
            "exemplar_morphology_id": morphology_id,
            "iteration": "test iteration",
            "score": 10,
            "seed": -1,
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def create_memodel_id(
    client,
    *,
    species_id,
    strain_id,
    brain_region_id,
    morphology_id,
    emodel_id,
    name="Test MEModel Name",
    description="Test MEModel Description",
    authorized_public: bool = False,
):
    response = client.post(
        ROUTES[MEModel],
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id),
            "species_id": str(species_id),
            "strain_id": str(strain_id),
            "morphology_id": str(morphology_id),
            "emodel_id": str(emodel_id),
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]
