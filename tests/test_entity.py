from app.db.model import IonChannelModel

from .utils import (
    PROJECT_ID,
    add_db,
    assert_request,
    create_brain_region,
    create_reconstruction_morphology_id,
)

ROUTE = "/entity"


def test_count_entities_validation_errors(client):
    """Test validation errors for the count endpoint."""
    response = client.get(f"{ROUTE}/counts")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/counts", params={"types": []})
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/counts", params={"types": "invalid_entity_type"})
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/counts", params={"types": "publication"})
    assert response.status_code == 422


def test_count_entities_by_type_single_type(client, morphology_id):  # noqa: ARG001
    """Test counting entities for a single entity type."""
    response = assert_request(
        client.get,
        url=f"{ROUTE}/counts",
        params={"types": "reconstruction_morphology"},
    )
    data = response.json()

    assert "reconstruction_morphology" in data
    assert data["reconstruction_morphology"] == 1


def test_count_entities_by_type_multiple_types(
    db,
    client,
    morphology_id,  # noqa: ARG001
    emodel_id,  # noqa: ARG001
    brain_region_id,
    species_id,
    person_id,
):
    """Test counting entities for multiple entity types."""
    add_db(
        db,
        IonChannelModel(
            name="test_ion_channel",
            description="test description",
            nmodl_suffix="test",
            temperature_celsius=20,
            neuron_block={},
            brain_region_id=brain_region_id,
            species_id=species_id,
            strain_id=None,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    response = assert_request(
        client.get,
        url=f"{ROUTE}/counts",
        params={"types": ["reconstruction_morphology", "emodel", "ion_channel_model"]},
    )
    data = response.json()

    assert "reconstruction_morphology" in data
    assert "emodel" in data
    assert "ion_channel_model" in data
    assert data["reconstruction_morphology"] == 1
    assert data["emodel"] == 1
    assert data["ion_channel_model"] == 1


def test_count_entities_by_type_zero_results(client):
    """Test counting entities when no entities exist for the requested types."""
    response = assert_request(
        client.get,
        url=f"{ROUTE}/counts",
        params={"types": "experimental_bouton_density"},
    )
    data = response.json()

    assert len(data) == 0


def test_count_entities_by_type_with_brain_region_filter(
    db, client, brain_region_hierarchy_id, species_id, person_id
):
    """Test counting entities with brain region filtering."""

    region1 = create_brain_region(
        db, brain_region_hierarchy_id, 1, "region1", created_by_id=person_id
    )
    region2 = create_brain_region(
        db, brain_region_hierarchy_id, 2, "region2", created_by_id=person_id
    )

    create_reconstruction_morphology_id(
        client,
        species_id=species_id,
        strain_id=None,
        brain_region_id=region1.id,
        authorized_public=False,
        name="morph1",
    )
    create_reconstruction_morphology_id(
        client,
        species_id=species_id,
        strain_id=None,
        brain_region_id=region2.id,
        authorized_public=False,
        name="morph2",
    )

    response = assert_request(
        client.get,
        url=f"{ROUTE}/counts",
        params={"types": "reconstruction_morphology"},
    )
    data = response.json()
    assert data["reconstruction_morphology"] == 2

    response = assert_request(
        client.get,
        url=f"{ROUTE}/counts",
        params={
            "types": "reconstruction_morphology",
            "within_brain_region_hierarchy_id": str(brain_region_hierarchy_id),
            "within_brain_region_brain_region_id": str(region1.id),
            "within_brain_region_ascendants": False,
        },
    )
    data = response.json()
    assert data["reconstruction_morphology"] == 1


def test_count_entities_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    species_id,
    strain_id,
    brain_region_id,
):
    """Test that entity counts respect authorization rules."""
    create_reconstruction_morphology_id(
        client_user_1,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
        name="private_morph",
    )

    create_reconstruction_morphology_id(
        client_user_1,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
        name="public_morph",
    )

    create_reconstruction_morphology_id(
        client_user_2,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
        name="user2_private_morph",
    )

    response = assert_request(
        client_user_1.get,
        url=f"{ROUTE}/counts",
        params={"types": "reconstruction_morphology"},
    )
    data = response.json()
    assert data["reconstruction_morphology"] == 2

    response = assert_request(
        client_user_2.get,
        url=f"{ROUTE}/counts",
        params={"types": "reconstruction_morphology"},
    )
    data = response.json()
    assert data["reconstruction_morphology"] == 2

    response = assert_request(
        client_no_project.get,
        url=f"{ROUTE}/counts",
        params={"types": "reconstruction_morphology"},
    )
    data = response.json()
    assert data["reconstruction_morphology"] == 1
