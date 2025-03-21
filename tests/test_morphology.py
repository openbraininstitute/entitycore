import itertools as it

from app.db.model import ReconstructionMorphology, Species, Strain

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    create_reconstruction_morphology_id,
)

ROUTE = "/reconstruction-morphology"


def test_create_reconstruction_morphology(
    client, species_id, strain_id, license_id, brain_region_id
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = client.post(
        ROUTE,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": morph_description,
            "name": morph_name,
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )
    assert response.status_code == 200, (
        f"Failed to create reconstruction morphology: {response.text}"
    )
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["species"]["id"] == species_id, (
        f"Failed to get species_id for reconstruction morphology: {data}"
    )
    assert data["strain"]["id"] == strain_id, (
        f"Failed to get strain_id for reconstruction morphology: {data}"
    )
    assert data["description"] == morph_description, (
        f"Failed to get description for reconstruction morphology: {data}"
    )
    assert data["name"] == morph_name, f"Failed to get name for reconstruction morphology: {data}"
    assert data["license"]["name"] == "Test License", (
        f"Failed to get license for reconstruction morphology: {data}"
    )

    response = client.get(ROUTE)
    assert response.status_code == 200, (
        f"Failed to get reconstruction morphologies: {response.text}"
    )


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_query_reconstruction_morphology(db, client, brain_region_id):  # noqa: PLR0915
    species1 = add_db(db, Species(name="TestSpecies1", taxonomy_id="0"))
    species2 = add_db(db, Species(name="TestSpecies2", taxonomy_id="1"))

    strain1 = add_db(db, Strain(name="TestStrain1", species_id=species1.id, taxonomy_id="0"))
    strain2 = add_db(db, Strain(name="TestStrain2", species_id=species2.id, taxonomy_id="1"))

    morphology_ids = []

    def create_morphologies(count):
        for i, (species, strain) in zip(
            range(count),
            it.cycle(
                (
                    (species1, strain1),
                    (species2, strain2),
                )
            ),
        ):
            morphology_id = create_reconstruction_morphology_id(
                client,
                species_id=species.id,
                strain_id=strain.id,
                brain_region_id=brain_region_id,
                authorized_public=False,
                name=f"Test Morphology Name {i}",
                description=f"Test Morphology Description {i}",
            )
            morphology_ids.append(morphology_id)

    count = 11
    create_morphologies(count)

    response = client.get(ROUTE, params={"page_size": 10})

    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(ROUTE, params={"page_size": 100, "order_by": "+creation_date"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11

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

    response = client.get(
        ROUTE,
        params={"order_by": "+creation_date", "page": 1, "page_size": 3},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [morphology_ids[i] for i in [0, 1, 2]]

    response = client.get(ROUTE, params={"with_facets": True})
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species1.id), "label": "TestSpecies1", "count": 6, "type": "species"},
            {"id": str(species2.id), "label": "TestSpecies2", "count": 5, "type": "species"},
        ],
        "strain": [
            {"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "strain"},
            {"id": str(strain2.id), "label": "TestStrain2", "count": 5, "type": "strain"},
        ],
    }

    response = client.get(ROUTE, params={"search": "Test", "with_facets": True})
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species1.id), "label": "TestSpecies1", "count": 6, "type": "species"},
            {"id": str(species2.id), "label": "TestSpecies2", "count": 5, "type": "species"},
        ],
        "strain": [
            {"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "strain"},
            {"id": str(strain2.id), "label": "TestStrain2", "count": 5, "type": "strain"},
        ],
    }

    response = client.get(ROUTE, params={"species__name": "TestSpecies1", "with_facets": True})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 6

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species1.id), "label": "TestSpecies1", "count": 6, "type": "species"}
        ],
        "strain": [{"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "strain"}],
    }


def test_query_reconstruction_morphology_species_join(db, client, brain_region_id):
    """Make sure not to join all the species w/ their strains while doing query"""
    species0 = add_db(db, Species(name="TestSpecies0", taxonomy_id="1"))
    strain0 = add_db(db, Strain(name="Strain0", taxonomy_id="strain0", species_id=species0.id))
    add_db(db, Strain(name="Strain1", taxonomy_id="strain1", species_id=species0.id))

    add_db(
        db,
        ReconstructionMorphology(
            brain_region_id=brain_region_id,
            species_id=species0.id,
            strain_id=strain0.id,
            description="description",
            name="morph00",
            location=None,
            legacy_id="Test Legacy ID",
            license_id=None,
            authorized_project_id=PROJECT_ID,
        ),
    )

    response = client.get(ROUTE, params={"with_facets": True})
    data = response.json()
    assert len(data["data"]) == data["pagination"]["total_items"]
    assert "facets" in data
    assert data["facets"] == {
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species0.id), "label": "TestSpecies0", "count": 1, "type": "species"}
        ],
        "strain": [{"id": str(strain0.id), "label": "Strain0", "count": 1, "type": "strain"}],
    }


def test_authorization(client_1, client_2, species_id, strain_id, license_id, brain_region_id):
    morph_json = {
        "location": {"x": 10, "y": 20, "z": 30},
        "brain_region_id": brain_region_id,
        "description": "morph description",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
        "name": "Test Morphology Name",
        "species_id": species_id,
        "strain_id": strain_id,
    }

    public_morph = client_1.post(
        ROUTE, json=morph_json | {"name": "public morphology", "authorized_public": True}
    )
    assert public_morph.status_code == 200
    public_morph = public_morph.json()

    inaccessible_obj = client_2.post(ROUTE, json=morph_json | {"name": "inaccessible morphology 1"})
    assert inaccessible_obj.status_code == 200
    inaccessible_obj = inaccessible_obj.json()

    private_morph0 = client_1.post(ROUTE, json=morph_json | {"name": "private morphology 0"})
    assert private_morph0.status_code == 200
    private_morph0 = private_morph0.json()

    private_morph1 = client_1.post(ROUTE, json=morph_json | {"name": "private morphology 1"})
    assert private_morph1.status_code == 200
    private_morph1 = private_morph1.json()

    # only return results that matches the desired project, and public ones
    response = client_1.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_morph["id"],
        private_morph0["id"],
        private_morph1["id"],
    }

    response = client_1.get(f"{ROUTE}/{inaccessible_obj['id']}")
    assert response.status_code == 404


def test_pagination(db, client, brain_region_id):
    species0 = add_db(db, Species(name="TestSpecies0", taxonomy_id="0"))
    species1 = add_db(db, Species(name="TestSpecies1", taxonomy_id="1"))
    strain0 = add_db(db, Strain(name="Strain0", taxonomy_id="strain0", species_id=species0.id))
    strain1 = add_db(db, Strain(name="Strain1", taxonomy_id="strain1", species_id=species1.id))

    total_items = 29
    for i, (species, strain) in zip(
        range(total_items), it.cycle(((species0, None), (species0, strain0), (species1, strain1)))
    ):
        create_reconstruction_morphology_id(
            client,
            species_id=species.id,
            strain_id=strain.id if strain else None,
            brain_region_id=brain_region_id,
            name=f"TestMorphologyName{i}",
            authorized_public=False,
        )

    response = client.get(ROUTE, params={"page_size": total_items + 1})

    assert response.status_code == 200
    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 10, 2):
        response = client.get(ROUTE, params={"page_size": i})

        assert response.status_code == 200
        data = response.json()["data"]
        expected_items = min(i, total_items)
        assert len(data) == expected_items
        names = [int(d["name"].removeprefix("TestMorphologyName")) for d in data]
        assert list(names) == list(range(total_items - 1, total_items - expected_items - 1, -1))

    items = []
    for i in range(1, total_items + 1):
        response = client.get(ROUTE, params={"page": i, "page_size": 1})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    names = [int(d["name"].removeprefix("TestMorphologyName")) for d in items]
    assert list(reversed(names)) == list(range(total_items))
