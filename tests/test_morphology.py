import itertools as it

import pytest

from app.db.model import ReconstructionMorphology, Species, Strain

from .utils import (
    BEARER_TOKEN,
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_HEADERS,
    add_db,
    assert_authorization,
    assert_dict_equal,
    assert_request,
    create_reconstruction_morphology_id,
)

ROUTE = "/reconstruction-morphology"


@pytest.mark.usefixtures("skip_project_check")
def test_create_reconstruction_morphology(
    client, species_id, strain_id, license_id, brain_region_id
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
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
    data = response.json()
    assert_dict_equal(
        data,
        {
            "name": morph_name,
            "description": morph_description,
            "brain_region.id": brain_region_id,
            "species.id": species_id,
            "strain.id": strain_id,
            "license.name": "Test License",
        },
    )
    response = assert_request(
        client.get, url=f"{ROUTE}/{data['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert_dict_equal(
        response.json(),
        {
            "name": morph_name,
            "description": morph_description,
            "brain_region.id": brain_region_id,
            "species.id": species_id,
            "strain.id": strain_id,
            "license.name": "Test License",
        },
    )


@pytest.mark.usefixtures("skip_project_check")
@pytest.mark.parametrize(
    ("route_id", "expected_status_code"),
    [
        (MISSING_ID, 404),
        (MISSING_ID_COMPACT, 404),
        ("42424242", 422),
        ("notanumber", 422),
    ],
)
def test_missing(client, route_id, expected_status_code):
    assert_request(
        client.get,
        url=f"{ROUTE}/{route_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=expected_status_code,
    )


@pytest.mark.usefixtures("skip_project_check")
def test_query_reconstruction_morphology(db, client, brain_region_id):
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
                species.id,
                strain.id,
                brain_region_id,
                headers=BEARER_TOKEN | PROJECT_HEADERS,
                authorized_public=False,
                name=f"Test Morphology Name {i}",
                description=f"Test Morphology Description {i}",
            )
            morphology_ids.append(morphology_id)

    count = 11
    create_morphologies(count)

    response = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": 100, "order_by": "+creation_date"},
    )
    data = response.json()["data"]
    assert len(data) == 11

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page_size": 100},
    )
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "-creation_date"},
    )
    data = response.json()["data"]
    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page": 1, "page_size": 3},
    )
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [morphology_ids[i] for i in [0, 1, 2]]

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
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

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"search": "Test", "with_facets": True},
    )
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

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"species__name": "TestSpecies1", "with_facets": True},
    )
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


@pytest.mark.usefixtures("skip_project_check")
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
            authorized_project_id=PROJECT_HEADERS["project-id"],
        ),
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
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


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, license_id, brain_region_id):
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
    assert_authorization(client=client, route=ROUTE, json_data=morph_json)


@pytest.mark.usefixtures("skip_project_check")
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
            species.id,
            strain.id if strain else None,
            brain_region_id,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            name=f"TestMorphologyName{i}",
            authorized_public=False,
        )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": total_items + 1},
    )

    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 10, 2):
        response = assert_request(
            client.get,
            url=ROUTE,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            params={"page_size": i},
        )

        data = response.json()["data"]
        expected_items = min(i, total_items)
        assert len(data) == expected_items
        names = [int(d["name"].removeprefix("TestMorphologyName")) for d in data]
        assert list(names) == list(range(total_items - 1, total_items - expected_items - 1, -1))

    items = []
    for i in range(1, total_items + 1):
        response = assert_request(
            client.get,
            url=ROUTE,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            params={"page": i, "page_size": 1},
        )

        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    names = [int(d["name"].removeprefix("TestMorphologyName")) for d in items]
    assert list(reversed(names)) == list(range(total_items))
