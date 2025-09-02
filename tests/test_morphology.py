import itertools as it

import pytest

from app.db.model import (
    Agent,
    Contribution,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.db.types import EntityType

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    count_db_class,
    create_reconstruction_morphology_id,
    delete_entity_classifications,
    delete_entity_contributions,
)

ROUTE = "/reconstruction-morphology"
ADMIN_ROUTE = "/admin/reconstruction-morphology"


@pytest.fixture
def json_data(species_id, strain_id, license_id, brain_region_id):
    return {
        "brain_region_id": str(brain_region_id),
        "species_id": str(species_id),
        "strain_id": str(strain_id),
        "description": "Test Morphology Description",
        "name": "Test Morphology Name",
        "location": {"x": 10, "y": 20, "z": 30},
        "legacy_id": ["Test Legacy ID"],
        "license_id": str(license_id),
    }


def test_create_reconstruction_morphology(
    client, species_id, strain_id, brain_region_id, json_data
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    assert data["brain_region"]["id"] == str(brain_region_id), (
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
    assert data["type"] == EntityType.reconstruction_morphology, (
        f"Failed to get correct type for reconstruction morphology: {data}"
    )
    assert data["created_by"]["id"] == data["updated_by"]["id"]

    response = client.get(ROUTE)
    assert response.status_code == 200, (
        f"Failed to get reconstruction morphologies: {response.text}"
    )
    data = response.json()["data"]
    assert data and all(item["type"] == EntityType.reconstruction_morphology for item in data), (  # noqa: PT018
        "One or more reconstruction morphologies has incorrect type"
    )
    assert data[0]["created_by"]["id"] == data[0]["updated_by"]["id"]


def test_delete_one(db, client, client_admin, morphology_id, person_id, role_id):
    model_id = morphology_id

    add_db(
        db,
        Contribution(
            agent_id=person_id,
            role_id=role_id,
            entity_id=model_id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    assert count_db_class(db, ReconstructionMorphology) == 1
    assert count_db_class(db, Contribution) == 1
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, MTypeClassification) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    delete_entity_contributions(client_admin, ROUTE, model_id)
    delete_entity_classifications(client, client_admin, model_id)

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, ReconstructionMorphology) == 0
    assert count_db_class(db, Contribution) == 0
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, MTypeClassification) == 0


def test_update_one(client, morphology_id):
    new_name = "my_new_name"
    new_description = "my_new_description"

    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{morphology_id}",
        json={
            "name": new_name,
            "description": new_description,
        },
    ).json()

    assert data["name"] == new_name
    assert data["description"] == new_description

    # set location
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{morphology_id}",
        json={
            "location": {"x": 100, "y": 200, "z": 300},
        },
    ).json()
    assert data["location"]["x"] == 100
    assert data["location"]["y"] == 200
    assert data["location"]["z"] == 300

    # unset location
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{morphology_id}",
        json={
            "location": None,
        },
    ).json()
    assert data["location"] is None


def test_update_one__public(client, json_data):
    # make private entity public
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data
        | {
            "authorized_public": True,
        },
    ).json()

    # should not be allowed to update it once public
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{data['id']}",
        json={"name": "foo"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_query_reconstruction_morphology(db, client, brain_region_id, person_id):
    species1 = add_db(
        db,
        Species(
            name="TestSpecies1", taxonomy_id="0", created_by_id=person_id, updated_by_id=person_id
        ),
    )
    species2 = add_db(
        db,
        Species(
            name="TestSpecies2", taxonomy_id="1", created_by_id=person_id, updated_by_id=person_id
        ),
    )

    strain1 = add_db(
        db,
        Strain(
            name="TestStrain1",
            species_id=species1.id,
            taxonomy_id="0",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    strain2 = add_db(
        db,
        Strain(
            name="TestStrain2",
            species_id=species2.id,
            taxonomy_id="1",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

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

    agent = db.get(Agent, db.get(ReconstructionMorphology, morphology_ids[0]).created_by_id)

    response = client.get(ROUTE, params={"page_size": 10})

    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10
    assert all(
        item["type"] == EntityType.reconstruction_morphology for item in response_json["data"]
    ), "One or more reconstruction morphologies has incorrect type"

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
        "brain_region": [
            {
                "count": 11,
                "id": str(brain_region_id),
                "label": "RedRegion",
                "type": "brain_region",
            },
        ],
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
        "created_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
        "updated_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
    }

    response = client.get(ROUTE, params={"search": "Test", "with_facets": True})
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "brain_region": [
            {"count": 11, "id": str(brain_region_id), "label": "RedRegion", "type": "brain_region"}
        ],
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
        "created_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
        "updated_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
    }

    response = client.get(ROUTE, params={"species__name": "TestSpecies1", "with_facets": True})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 6

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "brain_region": [
            {"count": 6, "id": str(brain_region_id), "label": "RedRegion", "type": "brain_region"}
        ],
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species1.id), "label": "TestSpecies1", "count": 6, "type": "species"}
        ],
        "strain": [{"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "strain"}],
        "created_by": [
            {
                "count": 6,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
        "updated_by": [
            {
                "count": 6,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": agent.type,
            },
        ],
    }


def test_query_reconstruction_morphology_species_join(db, client, brain_region_id, person_id):
    """Make sure not to join all the species w/ their strains while doing query"""
    species0 = add_db(
        db,
        Species(
            name="TestSpecies0", taxonomy_id="1", created_by_id=person_id, updated_by_id=person_id
        ),
    )
    strain0 = add_db(
        db,
        Strain(
            name="Strain0",
            taxonomy_id="strain0",
            species_id=species0.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    add_db(
        db,
        Strain(
            name="Strain1",
            taxonomy_id="strain1",
            species_id=species0.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    registered = assert_request(
        client.post,
        url=ROUTE,
        json={
            "brain_region_id": str(brain_region_id),
            "species_id": str(species0.id),
            "strain_id": str(strain0.id),
            "description": "description",
            "name": "morph00",
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": ["Test Legacy ID"],
        },
    ).json()

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()
    assert len(data["data"]) == data["pagination"]["total_items"]
    assert "facets" in data
    assert data["facets"] == {
        "brain_region": [
            {"count": 1, "id": str(brain_region_id), "label": "RedRegion", "type": "brain_region"}
        ],
        "contribution": [],
        "mtype": [],
        "species": [
            {"id": str(species0.id), "label": "TestSpecies0", "count": 1, "type": "species"}
        ],
        "strain": [{"id": str(strain0.id), "label": "Strain0", "count": 1, "type": "strain"}],
        "created_by": [
            {
                "count": 1,
                "id": registered["created_by"]["id"],
                "label": registered["created_by"]["pref_label"],
                "type": registered["created_by"]["type"],
            },
        ],
        "updated_by": [
            {
                "count": 1,
                "id": registered["created_by"]["id"],
                "label": registered["created_by"]["pref_label"],
                "type": registered["created_by"]["type"],
            },
        ],
    }


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    species_id,
    strain_id,
    license_id,
    brain_region_id,
):
    json_data = {
        "location": {"x": 10, "y": 20, "z": 30},
        "brain_region_id": str(brain_region_id),
        "description": "morph description",
        "legacy_id": ["Test Legacy ID"],
        "license_id": license_id,
        "name": "Test Morphology Name",
        "species_id": species_id,
        "strain_id": strain_id,
    }
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(db, client, brain_region_id, person_id):
    species0 = add_db(
        db,
        Species(
            name="TestSpecies0", taxonomy_id="0", created_by_id=person_id, updated_by_id=person_id
        ),
    )
    species1 = add_db(
        db,
        Species(
            name="TestSpecies1", taxonomy_id="1", created_by_id=person_id, updated_by_id=person_id
        ),
    )
    strain0 = add_db(
        db,
        Strain(
            name="Strain0",
            taxonomy_id="strain0",
            species_id=species0.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    strain1 = add_db(
        db,
        Strain(
            name="Strain1",
            taxonomy_id="strain1",
            species_id=species1.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    total_items = 3
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
    data = response.json()["data"]
    assert len(data) == total_items
    assert all(item["type"] == EntityType.reconstruction_morphology for item in data), (
        "One or more reconstruction morphologies has incorrect type"
    )

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


def test_filter_by_id__in(db, client, brain_region_id, person_id):
    """Test filtering reconstruction morphologies by id__in parameter."""
    species = add_db(
        db,
        Species(
            name="TestSpeciesFilter",
            taxonomy_id="0",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    strain = add_db(
        db,
        Strain(
            name="TestStrainFilter",
            species_id=species.id,
            taxonomy_id="0",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    morphology_ids = []
    for i in range(5):
        morphology_id = create_reconstruction_morphology_id(
            client,
            species_id=species.id,
            strain_id=strain.id,
            brain_region_id=brain_region_id,
            authorized_public=False,
            name=f"Filter Test Morphology {i}",
            description=f"Filter Test Description {i}",
        )
        mtype = add_db(
            db,
            MTypeClass(
                pref_label=f"m{i}",
                alt_label=f"m{i}",
                definition="d",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        add_db(
            db,
            MTypeClassification(
                entity_id=morphology_id,
                mtype_class_id=mtype.id,
                created_by_id=person_id,
                updated_by_id=person_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        )
        morphology_ids.append(morphology_id)

    # filtering by a single ID
    response = client.get(ROUTE, params={"id__in": morphology_ids[0]})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == morphology_ids[0]
    assert data[0]["type"] == EntityType.reconstruction_morphology, (
        "Filtered morphology has incorrect type"
    )

    # filtering by multiple IDs
    selected_ids = [morphology_ids[1], morphology_ids[3]]

    # backwards compat
    response = client.get(ROUTE, params={"id__in": ",".join(selected_ids)})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    returned_ids = [item["id"] for item in data]
    assert set(returned_ids) == set(selected_ids)

    response = client.get(ROUTE, params={"id__in": selected_ids})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    returned_ids = [item["id"] for item in data]
    assert set(returned_ids) == set(selected_ids)

    # filtering by all IDs

    # backwards compat
    response = client.get(ROUTE, params={"id__in": ",".join(morphology_ids)})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 5
    returned_ids = [item["id"] for item in data]
    assert set(returned_ids) == set(morphology_ids)

    response = client.get(ROUTE, params={"id__in": morphology_ids})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 5
    returned_ids = [item["id"] for item in data]
    assert set(returned_ids) == set(morphology_ids)

    # filtering by non-existent ID
    response = client.get(ROUTE, params={"id__in": MISSING_ID})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 0

    # combining id__in with other filters

    # backwards compat
    response = client.get(
        ROUTE,
        params={"id__in": ",".join(morphology_ids), "name__ilike": "%Filter Test Morphology 2%"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == morphology_ids[2]

    response = client.get(
        ROUTE,
        params={"id__in": morphology_ids, "name__ilike": "%Filter Test Morphology 2%"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == morphology_ids[2]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"mtype__pref_label__in": ["m1", "m2"], "order_by": "mtype__pref_label"},
    ).json()["data"]
    assert [d["mtypes"][0]["pref_label"] for d in data] == ["m1", "m2"]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"mtype__pref_label__in": ["m1", "m2"], "order_by": "-mtype__pref_label"},
    ).json()["data"]
    assert [d["mtypes"][0]["pref_label"] for d in data] == ["m2", "m1"]


def test_brain_region_filter(db, client, brain_region_hierarchy_id, species_id, person_id):
    def create_model_function(_db, name, brain_region_id):
        return ReconstructionMorphology(
            name=name,
            brain_region_id=brain_region_id,
            species_id=species_id,
            strain_id=None,
            description="description",
            location=None,
            legacy_id="Test Legacy ID",
            license_id=None,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)
