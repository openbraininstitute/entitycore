from datetime import timedelta
from unittest.mock import ANY

import pytest

from app.db.model import ElectricalCellRecording, Species, Subject
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_missing,
    create_brain_region,
    create_electrical_cell_recording_db,
    create_electrical_cell_recording_id,
)

ROUTE = "electrical-cell-recording"


def test_create_one(
    client, subject_id, license_id, brain_region_id, electrical_cell_recording_json_data
):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=electrical_cell_recording_json_data,
    ).json()

    assert data["name"] == "my-name"
    assert data["description"] == "my-description"
    assert data["subject"]["id"] == str(subject_id)
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["license"]["id"] == str(license_id)
    assert data["authorized_project_id"] == str(PROJECT_ID)
    assert data["type"] == EntityType.electrical_cell_recording
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["etypes"] == []


def test_read_one(client, subject_id, license_id, brain_region_id, trace_id_with_assets):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{trace_id_with_assets}",
    ).json()

    assert data["name"] == "my-name"
    assert data["description"] == "my-description"
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["subject"]["id"] == str(subject_id)
    assert data["license"]["id"] == str(license_id)
    assert data["authorized_project_id"] == PROJECT_ID
    assert len(data["stimuli"]) == 2
    assert len(data["assets"]) == 1
    assert data["type"] == EntityType.electrical_cell_recording
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["etypes"] == [
        {
            "id": ANY,
            "pref_label": "etype-pref-label",
            "alt_label": "etype-alt-label",
            "definition": "etype-definition",
            "creation_date": ANY,
            "update_date": ANY,
        },
    ]


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1, client_user_2, client_no_project, electrical_cell_recording_json_data
):
    check_authorization(
        ROUTE, client_user_1, client_user_2, client_no_project, electrical_cell_recording_json_data
    )


def test_pagination(client, electrical_cell_recording_json_data):
    _ = [
        create_electrical_cell_recording_id(
            client, json_data=electrical_cell_recording_json_data | {"name": f"entity-{i}"}
        )
        for i in range(2)
    ]
    response = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 1},
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 1


@pytest.fixture
def faceted_ids(
    db, client, brain_region_hierarchy_id, electrical_cell_recording_json_data, person_id
):
    brain_region_ids = [
        create_brain_region(
            db,
            brain_region_hierarchy_id,
            annotation_value=i,
            name=f"region-{i}",
            created_by_id=person_id,
        ).id
        for i in range(2)
    ]

    trace_ids = [
        create_electrical_cell_recording_id(
            client,
            json_data=electrical_cell_recording_json_data
            | {
                "name": f"trace-{i}",
                "description": f"brain-region-{i}",
                "brain_region_id": str(region_id),
            },
        )
        for i, region_id in enumerate(brain_region_ids)
    ]
    return brain_region_ids, trace_ids


def test_facets(client, faceted_ids):
    brain_region_ids, _ = faceted_ids

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["contribution"] == []
    assert facets["brain_region"] == [
        {"id": str(brain_region_ids[0]), "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": str(brain_region_ids[1]), "label": "region-1", "count": 1, "type": "brain_region"},
    ]
    assert facets["etype"] == []
    assert facets["species"] == [
        {"id": ANY, "label": "Test Species", "count": 2, "type": "subject.species"}
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"search": "brain-region-0", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["brain_region"] == [
        {"id": ANY, "label": "region-0", "count": 1, "type": "brain_region"},
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"brain_region__name": "region-0", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["brain_region"] == [
        {"id": ANY, "label": "region-0", "count": 1, "type": "brain_region"},
    ]


def test_brain_region_filter(
    db, client, brain_region_hierarchy_id, electrical_cell_recording_json_data
):
    def create_model_function(_db, name, brain_region_id):
        return create_electrical_cell_recording_db(
            db,
            client,
            json_data=electrical_cell_recording_json_data
            | {"name": name, "brain_region_id": str(brain_region_id)},
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_filtering(db, client, electrical_cell_recording_json_data, person_id):
    species = add_all_db(
        db,
        [
            Species(
                name=f"species-{i}",
                taxonomy_id=f"taxonomy-{i}",
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for i in range(3)
        ],
    )
    subjects = add_all_db(
        db,
        [
            Subject(
                name=f"subject-{i}",
                description="my-description",
                species_id=sp.id,
                strain_id=None,
                age_value=timedelta(days=14),
                age_period="postnatal",
                sex="female",
                weight=1.5,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for i, sp in enumerate(species + species)
        ],
    )

    models = add_all_db(
        db,
        [
            ElectricalCellRecording(
                **electrical_cell_recording_json_data
                | {
                    "subject_id": str(subject.id),
                    "name": f"e-{i}",
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "authorized_project_id": PROJECT_ID,
                }
            )
            for i, subject in enumerate(subjects)
        ],
    )
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get, url=ROUTE, params=f"subject__species__id={species[1].id}"
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(client.get, url=ROUTE, params="subject__species__name=species-2").json()[
        "data"
    ]
    assert len(data) == 2

    data = assert_request(client.get, url=ROUTE, params="subject__species__name=species-2").json()[
        "data"
    ]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"name__in": ["e-1", "e-2"]},
    ).json()["data"]
    assert {d["name"] for d in data} == {"e-1", "e-2"}

    # backwards compat
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"name__in": "e-1,e-2"},
    ).json()["data"]
    assert {d["name"] for d in data} == {"e-1", "e-2"}
