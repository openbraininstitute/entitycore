from unittest.mock import ANY

import pytest

from app.db.model import ElectricalCellRecording, ElectricalRecordingStimulus
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_missing,
    create_asset_file,
    create_brain_region,
)

MODEL = ElectricalCellRecording
ROUTE = "electrical-cell-recording"


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id):
    return {
        "name": "my-name",
        "description": "my-description",
        "subject_id": subject_id,
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
        "recording_location": ["soma[0]_0.5"],
        "recording_type": "intracellular",
        "recording_origin": "in_vivo",
        "ljp": 11.5,
        "authorized_public": False,
    }


@pytest.fixture
def create(client, json_data):
    def _create(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()

    return _create


@pytest.fixture
def create_id(create):
    def _create_id(**kwargs):
        return create(**kwargs)["id"]

    return _create_id


@pytest.fixture
def create_db(db, create_id):
    def _create_db(**kwargs):
        return db.get(MODEL, create_id(**kwargs))

    return _create_db


def _create_electrical_recording_id(
    db,
    recording_id,
):
    return add_db(
        db,
        ElectricalRecordingStimulus(
            name="protocol",
            description="protocol-description",
            dt=0.1,
            injection_type="current_clamp",
            shape="sinusoidal",
            start_time=0.0,
            end_time=1.0,
            recording_id=recording_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    ).id


@pytest.fixture
def trace_id(tmp_path, client, db, create_id):
    trace_id = create_id()

    # add two protocols that refer to it
    _create_electrical_recording_id(db, trace_id)
    _create_electrical_recording_id(db, trace_id)

    filepath = tmp_path / "trace.nwb"
    filepath.write_bytes(b"trace")

    # add an asset too
    create_asset_file(
        client=client,
        entity_type="electrical_cell_recording",
        entity_id=trace_id,
        file_name="my-trace.nwb",
        file_obj=filepath.read_bytes(),
    )

    return trace_id


def test_create_one(client, subject_id, license_id, brain_region_id, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()

    assert data["name"] == "my-name"
    assert data["description"] == "my-description"
    assert data["subject"]["id"] == str(subject_id)
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["license"]["id"] == str(license_id)
    assert data["authorized_project_id"] == str(PROJECT_ID)
    assert data["type"] == EntityType.electrical_cell_recording
    assert data["created_by"]["id"] == data["updated_by"]["id"]


def test_read_one(client, subject_id, license_id, brain_region_id, trace_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{trace_id}",
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


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    _ = [create_id(name=f"entity-{i}") for i in range(2)]
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
def faceted_ids(db, brain_region_hierarchy_id, create_id):
    brain_region_ids = [
        create_brain_region(
            db, brain_region_hierarchy_id, annotation_value=i, name=f"region-{i}"
        ).id
        for i in range(2)
    ]

    trace_ids = [
        create_id(
            name=f"trace-{i}", description=f"brain-region-{i}", brain_region_id=str(region_id)
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


def test_brain_region_filter(db, client, brain_region_hierarchy_id, create_db):
    def create_model_function(_db, name, brain_region_id):
        return create_db(name=name, brain_region_id=str(brain_region_id))

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)
