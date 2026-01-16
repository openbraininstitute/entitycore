import itertools as it
from datetime import timedelta
from unittest.mock import ANY

import pytest

from app.db.model import (
    Agent,
    Annotation,
    Asset,
    CellMorphology,
    CellMorphologyProtocol,
    Contribution,
    EmbeddingMixin,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
    MeasurementLabel,
    MTypeClass,
    MTypeClassification,
    Species,
    Strain,
    Subject,
)
from app.db.types import EntityType

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    USER_SUB_ID_1,
    add_annotation,
    add_contribution,
    add_db,
    add_measurement_annotation,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_deletion_cascades,
    check_entity_delete_one,
    check_entity_update_one,
    create_cell_morphology_id,
    create_mtype_classification,
    upload_entity_asset,
)

ROUTE = "/cell-morphology"
ADMIN_ROUTE = "/admin/cell-morphology"


@pytest.fixture
def json_data(subject_id, license_id, brain_region_id, cell_morphology_protocol):
    return {
        "brain_region_id": str(brain_region_id),
        "subject_id": str(subject_id),
        "description": "Test Morphology Description",
        "name": "Test Morphology Name",
        "location": {"x": 10, "y": 20, "z": 30},
        "legacy_id": ["Test Legacy ID"],
        "license_id": str(license_id),
        "cell_morphology_protocol_id": str(cell_morphology_protocol.id),
        "contact_email": "test@example.com",
        "notice_text": "Notice text example",
        "experiment_date": "2025-01-01T00:00:00",
        "repair_pipeline_state": "raw",
    }


def test_create_one(
    client,
    brain_region_id,
    subject_id,
    json_data,
    cell_morphology_protocol_json_data,
):
    expected_cell_morphology_protocol_json_data = cell_morphology_protocol_json_data | {"id": ANY}

    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for cell morphology: {data}"
    )
    assert data["subject"]["id"] == subject_id, (
        f"Failed to get subject_id for cell morphology: {data}"
    )
    assert data["description"] == morph_description, (
        f"Failed to get description for cell morphology: {data}"
    )
    assert data["name"] == morph_name, f"Failed to get name for cell morphology: {data}"
    assert data["license"]["name"] == "Test License", (
        f"Failed to get license for cell morphology: {data}"
    )
    assert data["type"] == EntityType.cell_morphology, (
        f"Failed to get correct type for cell morphology: {data}"
    )
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["contact_email"] == "test@example.com"
    assert data["experiment_date"] == "2025-01-01T00:00:00"
    assert data["notice_text"] == "Notice text example"
    assert data["cell_morphology_protocol"] == expected_cell_morphology_protocol_json_data
    assert not data["has_segmented_spines"]
    assert data["repair_pipeline_state"] == "raw"

    response = client.get(ROUTE)
    assert response.status_code == 200, f"Failed to get cell morphologies: {response.text}"
    data = response.json()["data"]
    assert data and all(item["type"] == EntityType.cell_morphology for item in data), (  # noqa: PT018
        "One or more cell morphologies has incorrect type"
    )
    assert data[0]["created_by"]["id"] == data[0]["updated_by"]["id"]
    assert data[0]["cell_morphology_protocol"] == expected_cell_morphology_protocol_json_data


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={CellMorphology: 1, CellMorphologyProtocol: 1},
        expected_counts_after={
            CellMorphology: 0,
            CellMorphologyProtocol: 1,
        },
    )


@pytest.fixture
def entity_id_cascades(db, clients, json_data, person_id, role_id, mtype_class_id):
    entity_id = add_db(
        db,
        CellMorphology(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    ).id
    add_contribution(
        db,
        entity_id=entity_id,
        agent_id=person_id,
        role_id=role_id,
        created_by_id=person_id,
    )
    create_mtype_classification(
        db,
        entity_id=entity_id,
        mtype_class_id=mtype_class_id,
        created_by_id=person_id,
    )
    add_annotation(
        db,
        entity_id=entity_id,
        created_by_id=person_id,
    )
    add_measurement_annotation(
        db,
        entity_id=entity_id,
        created_by_id=person_id,
        entity_type="cell_morphology",
    )
    upload_entity_asset(
        client=clients.user_1,
        entity_type=EntityType.cell_morphology,
        entity_id=entity_id,
        files={"file": ("cell.swc", b"foo", "application/swc")},
        label="morphology",
    )
    return entity_id


def test_deletion_cascades(db, clients, entity_id_cascades):
    check_deletion_cascades(
        db=db,
        route=ROUTE,
        clients=clients,
        entity_id=entity_id_cascades,
        expected_counts_before={
            Annotation: 1,
            Asset: 1,
            CellMorphology: 1,
            CellMorphologyProtocol: 1,
            Contribution: 1,
            MeasurementAnnotation: 1,
            MeasurementKind: 1,
            MeasurementItem: 1,
            MeasurementLabel: 1,
            MTypeClass: 1,
            MTypeClassification: 1,
        },
        expected_counts_after={
            Annotation: 0,
            Asset: 0,
            CellMorphology: 0,
            CellMorphologyProtocol: 1,
            Contribution: 0,
            MeasurementAnnotation: 0,
            MeasurementKind: 0,
            MeasurementItem: 0,
            MeasurementLabel: 1,
            MTypeClass: 1,
            MTypeClassification: 0,
        },
    )


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
        },
        optional_payload={
            "location": {"x": 100, "y": 200, "z": 300},
        },
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


def test_query_cell_morphology(db, client, brain_region_id, person_id):
    species1 = add_db(
        db,
        Species(
            name="TestSpecies1",
            taxonomy_id="0",
            created_by_id=person_id,
            updated_by_id=person_id,
            embedding=EmbeddingMixin.SIZE * [0.1],
        ),
    )
    species2 = add_db(
        db,
        Species(
            name="TestSpecies2",
            taxonomy_id="1",
            created_by_id=person_id,
            updated_by_id=person_id,
            embedding=EmbeddingMixin.SIZE * [0.1],
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
            embedding=EmbeddingMixin.SIZE * [0.1],
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
            embedding=EmbeddingMixin.SIZE * [0.1],
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
            subject = add_db(
                db,
                Subject(
                    name=f"subject-{i}",
                    description=f"my-description-{i}",
                    species_id=species.id,
                    strain_id=strain.id,
                    age_value=timedelta(days=14),
                    age_period="postnatal",
                    sex="male",
                    weight=1.5,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            )
            morphology_id = create_cell_morphology_id(
                client,
                subject_id=str(subject.id),
                brain_region_id=brain_region_id,
                authorized_public=False,
                name=f"Test Morphology Name {i}",
                description=f"Test Morphology Description {i}",
            )
            morphology_ids.append(morphology_id)

    count = 11
    create_morphologies(count)

    agent = db.get(Agent, db.get(CellMorphology, morphology_ids[0]).created_by_id)

    response = client.get(ROUTE, params={"page_size": 10})

    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10
    assert all(item["type"] == EntityType.cell_morphology for item in response_json["data"]), (
        "One or more cell morphologies has incorrect type"
    )

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
            {
                "id": str(species1.id),
                "label": "TestSpecies1",
                "count": 6,
                "type": "subject.species",
            },
            {
                "id": str(species2.id),
                "label": "TestSpecies2",
                "count": 5,
                "type": "subject.species",
            },
        ],
        "strain": [
            {"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "subject.strain"},
            {"id": str(strain2.id), "label": "TestStrain2", "count": 5, "type": "subject.strain"},
        ],
        "created_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "updated_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "cell_morphology_protocol": [],
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
            {
                "id": str(species1.id),
                "label": "TestSpecies1",
                "count": 6,
                "type": "subject.species",
            },
            {
                "id": str(species2.id),
                "label": "TestSpecies2",
                "count": 5,
                "type": "subject.species",
            },
        ],
        "strain": [
            {"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "subject.strain"},
            {"id": str(strain2.id), "label": "TestStrain2", "count": 5, "type": "subject.strain"},
        ],
        "created_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "updated_by": [
            {
                "count": 11,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "cell_morphology_protocol": [],
    }

    response = client.get(
        ROUTE, params={"subject__species__name": "TestSpecies1", "with_facets": True}
    )
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
            {"id": str(species1.id), "label": "TestSpecies1", "count": 6, "type": "subject.species"}
        ],
        "strain": [
            {"id": str(strain1.id), "label": "TestStrain1", "count": 6, "type": "subject.strain"}
        ],
        "created_by": [
            {
                "count": 6,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "updated_by": [
            {
                "count": 6,
                "id": str(agent.id),
                "label": agent.pref_label,
                "type": str(agent.type),
            },
        ],
        "cell_morphology_protocol": [],
    }


def test_query_cell_morphology_species_join(db, client, brain_region_id, subject_id):
    """Make sure not to join all the species w/ their strains while doing query"""

    subject = db.get(Subject, subject_id)

    registered = assert_request(
        client.post,
        url=ROUTE,
        json={
            "brain_region_id": str(brain_region_id),
            "subject_id": str(subject_id),
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
            {
                "id": str(subject.species.id),
                "label": subject.species.name,
                "count": 1,
                "type": "subject.species",
            }
        ],
        "strain": [
            {
                "id": str(subject.strain.id),
                "label": subject.strain.name,
                "count": 1,
                "type": "subject.strain",
            }
        ],
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
        "cell_morphology_protocol": [],
    }


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    subject_id,
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
        "subject_id": str(subject_id),
    }
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(db, client, brain_region_id, person_id):
    species0 = add_db(
        db,
        Species(
            name="TestSpecies0",
            taxonomy_id="0",
            created_by_id=person_id,
            updated_by_id=person_id,
            embedding=EmbeddingMixin.SIZE * [0.1],
        ),
    )
    species1 = add_db(
        db,
        Species(
            name="TestSpecies1",
            taxonomy_id="1",
            created_by_id=person_id,
            updated_by_id=person_id,
            embedding=EmbeddingMixin.SIZE * [0.1],
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
            embedding=EmbeddingMixin.SIZE * [0.1],
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
            embedding=EmbeddingMixin.SIZE * [0.1],
        ),
    )

    total_items = 3
    for i, (species, strain) in zip(
        range(total_items), it.cycle(((species0, None), (species0, strain0), (species1, strain1)))
    ):
        subject = add_db(
            db,
            Subject(
                name=f"subject-{i}",
                description=f"my-description-{i}",
                species_id=species.id,
                strain_id=strain.id if strain else None,
                age_value=timedelta(days=14),
                age_period="postnatal",
                sex="male",
                weight=1.5,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        create_cell_morphology_id(
            client,
            subject_id=str(subject.id),
            brain_region_id=brain_region_id,
            name=f"TestMorphologyName{i}",
            authorized_public=False,
        )

    response = client.get(ROUTE, params={"page_size": total_items + 1})

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == total_items
    assert all(item["type"] == EntityType.cell_morphology for item in data), (
        "One or more cell morphologies has incorrect type"
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


def test_filter_by_id__in(db, client, brain_region_id, person_id, subject_id):
    """Test filtering cell morphologies by id__in parameter."""
    morphology_ids = []
    for i in range(5):
        morphology_id = create_cell_morphology_id(
            client,
            subject_id=str(subject_id),
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
    assert data[0]["type"] == EntityType.cell_morphology, "Filtered morphology has incorrect type"

    # filtering by multiple IDs
    selected_ids = [morphology_ids[1], morphology_ids[3]]
    response = client.get(ROUTE, params={"id__in": selected_ids})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    returned_ids = [item["id"] for item in data]
    assert set(returned_ids) == set(selected_ids)

    # filtering by all IDs
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

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1},
    ).json()["data"]
    assert len(data) == 5

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*Description*"},
    ).json()["data"]
    assert len(data) == 5

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*Morphology 2"},
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*Filter*Morphology*"},
    ).json()["data"]
    assert len(data) == 5

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "Filter Morphology_2"},
    ).json()["data"]
    assert len(data) == 0


def test_brain_region_filter(db, client, brain_region_hierarchy_id, person_id, subject_id):
    def create_model_function(_db, name, brain_region_id):
        return CellMorphology(
            name=name,
            brain_region_id=brain_region_id,
            subject_id=subject_id,
            description="description",
            location=None,
            legacy_id="Test Legacy ID",
            license_id=None,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
            cell_morphology_protocol_id=None,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)
