from datetime import timedelta
from unittest.mock import ANY

import pytest

from app.db.model import (
    BrainRegion,
    ElectricalCellRecording,
    ETypeClass,
    ETypeClassification,
    Species,
    Subject,
)
from app.db.types import ElectricalRecordingOrigin, ElectricalRecordingType, EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_update_one,
    check_missing,
    create_brain_region,
    create_electrical_cell_recording_db,
    create_electrical_cell_recording_id,
)

ROUTE = "/electrical-cell-recording"
ADMIN_ROUTE = f"/admin{ROUTE}"


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


def test_update_one(clients, electrical_cell_recording_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=electrical_cell_recording_json_data,
        patch_payload={
            "name": "name",
            "description": "description",
        },
        optional_payload={
            "temperature": 10.0,
        },
    )


def test_user_read_one(client, subject_id, license_id, brain_region_id, trace_id_with_assets):
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


def test_admin_read_one(
    client_admin, subject_id, license_id, brain_region_id, trace_id_with_assets
):
    data = assert_request(
        client_admin.get,
        url=f"{ADMIN_ROUTE}/{trace_id_with_assets}",
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


def _delete_stimuli(client_admin, trace_id):
    data = assert_request(
        client_admin.get,
        url=f"{ROUTE}/{trace_id}",
    ).json()

    for stimulus in data["stimuli"]:
        stimulus_id = stimulus["id"]
        data = assert_request(
            client_admin.delete,
            url=f"/admin/electrical-recording-stimulus/{stimulus_id}",
        ).json()


def test_delete_one(db, clients, electrical_cell_recording_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=electrical_cell_recording_json_data,
        expected_counts_before={
            ElectricalCellRecording: 1,
        },
        expected_counts_after={
            ElectricalCellRecording: 0,
        },
    )


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


@pytest.fixture
def models(db, electrical_cell_recording_json_data, person_id, brain_region_hierarchy_id):
    species = add_all_db(
        db,
        [
            Species(
                name=f"species-{i}",
                taxonomy_id=f"taxonomy-{i}",
                created_by_id=person_id,
                updated_by_id=person_id,
                embedding=1536 * [0.1],
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

    brain_regions = add_all_db(
        db,
        [
            BrainRegion(
                annotation_value=i,
                acronym=f"acronym-{i}",
                name=f"region-{i}",
                color_hex_triplet="FF0000",
                parent_structure_id=None,
                hierarchy_id=brain_region_hierarchy_id,
                created_by_id=person_id,
                updated_by_id=person_id,
                embedding=1536 * [0.1],
            )
            for i in range(len(subjects))
        ],
    )

    recordings = []
    recordings_ids = [0, 1, 1, 1, 2, 2]
    recording_types = [
        ElectricalRecordingType.extracellular,
        ElectricalRecordingType.intracellular,
        ElectricalRecordingType.both,
        ElectricalRecordingType.unknown,
        ElectricalRecordingType.extracellular,
        ElectricalRecordingType.extracellular,
    ]
    recording_origins = [
        ElectricalRecordingOrigin.in_silico,
        ElectricalRecordingOrigin.in_vitro,
        ElectricalRecordingOrigin.in_vivo,
        ElectricalRecordingOrigin.unknown,
        ElectricalRecordingOrigin.in_silico,
        ElectricalRecordingOrigin.in_silico,
    ]
    for i, (subject, recordings_id, recording_type, recording_origin) in enumerate(
        zip(subjects, recordings_ids, recording_types, recording_origins, strict=True)
    ):
        rec = add_db(
            db,
            ElectricalCellRecording(
                **electrical_cell_recording_json_data
                | {
                    "subject_id": str(subject.id),
                    "name": f"e-{recordings_id}",
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "authorized_project_id": PROJECT_ID,
                    "brain_region_id": brain_regions[i].id,
                    "recording_type": recording_type,
                    "recording_origin": recording_origin,
                }
            ),
        )
        etype = add_db(
            db,
            ETypeClass(
                pref_label=f"e{i}",
                alt_label=f"e{i}",
                definition="d",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        add_db(
            db,
            ETypeClassification(
                entity_id=rec.id,
                etype_class_id=etype.id,
                created_by_id=person_id,
                updated_by_id=person_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        )

        recordings.append(rec)

    return species, subjects, recordings


def test_filtering(client, models):
    species, _, recordings = models

    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(recordings)

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

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"recording_type": ElectricalRecordingType.intracellular},
    ).json()["data"]
    assert len(data) == 1
    assert all(d["recording_type"] == ElectricalRecordingType.intracellular for d in data)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"recording_type": ElectricalRecordingType.extracellular},
    ).json()["data"]
    assert len(data) == 3
    assert all(d["recording_type"] == ElectricalRecordingType.extracellular for d in data)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "recording_type__in": [
                ElectricalRecordingType.intracellular,
                ElectricalRecordingType.extracellular,
            ]
        },
    ).json()["data"]
    assert len(data) == 4

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"recording_origin": ElectricalRecordingOrigin.in_vivo},
    ).json()["data"]
    assert len(data) == 1
    assert all(d["recording_origin"] == ElectricalRecordingOrigin.in_vivo for d in data)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"recording_origin": ElectricalRecordingOrigin.in_silico},
    ).json()["data"]
    assert len(data) == 3
    assert all(d["recording_origin"] == ElectricalRecordingOrigin.in_silico for d in data)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "recording_origin__in": [
                ElectricalRecordingOrigin.in_vivo,
                ElectricalRecordingOrigin.in_silico,
            ]
        },
    ).json()["data"]
    assert len(data) == 4


def test_sorting(client, models):
    _, _, recordings = models

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    # default: ascending by date
    data = req("order_by=creation_date")
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings]

    # equivalent to above
    data = req({"order_by": ["creation_date"]})
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings]

    # ascending by date
    data = req("order_by=creation_date")
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings]

    # equivalent to above
    data = req({"order_by": "+creation_date"})
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings]

    # descending by date
    data = req("order_by=-creation_date")
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings][::-1]

    # equivalent to above
    data = req({"order_by": ["-creation_date"]})
    assert len(data) == len(recordings)
    assert [d["id"] for d in data] == [str(m.id) for m in recordings][::-1]

    # ascending by name
    data = req("order_by=name")
    assert len(data) == len(recordings)
    assert [d["name"] for d in data] == [f"e-{i}" for i in (0, 1, 1, 1, 2, 2)]

    # descending by name
    data = req("order_by=-name")
    assert len(data) == len(recordings)
    assert [d["name"] for d in data] == [f"e-{i}" for i in (2, 2, 1, 1, 1, 0)]

    # ascending by species name
    data = req("order_by=subject__species__name")
    assert [d["subject"]["species"]["name"] for d in data] == [
        f"species-{i}" for i in (0, 0, 1, 1, 2, 2)
    ]

    # descending by species name
    data = req("order_by=-subject__species__name")
    assert [d["subject"]["species"]["name"] for d in data] == [
        f"species-{i}" for i in (2, 2, 1, 1, 0, 0)
    ]

    # ascending by brain region acronym
    data = req("order_by=brain_region__acronym")
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in (0, 1, 2, 3, 4, 5)
    ]

    # descending by brain region acronym
    data = req("order_by=-brain_region__acronym")
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in (5, 4, 3, 2, 1, 0)
    ]

    # brain region acronym should sort name ties in desc order
    data = req({"order_by": ["+name", "-brain_region__acronym"]})
    assert [d["name"] for d in data] == [f"e-{i}" for i in [0, 1, 1, 1, 2, 2]]
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in [0, 3, 2, 1, 5, 4]
    ]

    # brain region acronym should sort name ties in asc order
    data = req({"order_by": ["+name", "+brain_region__acronym"]})
    assert [d["name"] for d in data] == [f"e-{i}" for i in [0, 1, 1, 1, 2, 2]]
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in [0, 1, 2, 3, 4, 5]
    ]

    # sort using two cols of the same model
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"order_by": ["+brain_region__name", "+brain_region__acronym"]},
    ).json()["data"]
    assert [d["brain_region"]["name"] for d in data] == [f"region-{i}" for i in [0, 1, 2, 3, 4, 5]]

    # one-to-many with one element
    data = req({"order_by": "etype__pref_label"})
    assert [d["etypes"][0]["pref_label"] for d in data] == [f"e{i}" for i in range(6)]

    data = req({"order_by": "-etype__pref_label"})
    assert [d["etypes"][0]["pref_label"] for d in data] == [f"e{i}" for i in range(6)][::-1]


def test_sorting_and_filtering(client, models):  # noqa: ARG001
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"name": "e-1", "order_by": "-brain_region__acronym"})
    assert [d["name"] for d in data] == ["e-1", "e-1", "e-1"]
    assert [d["brain_region"]["acronym"] for d in data] == ["acronym-3", "acronym-2", "acronym-1"]

    data = req(
        {
            "subject__species__name__in": ["species-1", "species-2"],
            "order_by": "-brain_region__acronym",
        }
    )
    assert [d["subject"]["species"]["name"] for d in data] == [
        "species-2",
        "species-1",
        "species-2",
        "species-1",
    ]
    assert [d["brain_region"]["acronym"] for d in data] == [
        "acronym-5",
        "acronym-4",
        "acronym-2",
        "acronym-1",
    ]

    data = req(
        {
            "subject__species__name__in": ["species-1", "species-2"],
            "order_by": "-etype__pref_label",
        }
    )
    assert [d["subject"]["species"]["name"] for d in data] == [
        "species-2",
        "species-1",
        "species-2",
        "species-1",
    ]
    assert [d["brain_region"]["acronym"] for d in data] == [
        "acronym-5",
        "acronym-4",
        "acronym-2",
        "acronym-1",
    ]
