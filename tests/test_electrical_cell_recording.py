import pytest

from app.db.model import ElectricalCellRecording

from .utils import (
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_missing,
    create_brain_region_id,
)

ROUTE = "electrical-cell-recording"


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id):
    return {
        "name": "my-name",
        "description": "my-description",
        "subject_id": str(subject_id),
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
        "recordingLocation": ["soma[0.5]"],
        "recordingType": "intracellular",
    }


def _create_electrical_cell_recording_id(
    db,
    *,
    subject_id,
    license_id,
    brain_region_id,
    name="my-name",
    ljp=11.5,
    description="my-description",
    recording_location=None,
    authorized_public=False,
    authorized_project_id=PROJECT_ID,
):
    if recording_location is None:
        recording_location = ["soma[0]_0.5"]

    return add_db(
        db,
        ElectricalCellRecording(
            name=name,
            description=description,
            license_id=str(license_id),
            brain_region_id=brain_region_id,
            subject_id=str(subject_id),
            ljp=ljp,
            recordingLocation=recording_location,
            recordingType="intracellular",
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
        ),
    ).id


@pytest.fixture
def trace_id(db, subject_id, brain_region_id, license_id):
    return _create_electrical_cell_recording_id(
        db,
        subject_id=subject_id,
        license_id=license_id,
        brain_region_id=brain_region_id,
    )


def test_create_one(client, subject_id, license_id, brain_region_id, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()

    assert data["name"] == "my-name"
    assert data["description"] == "my-description"
    assert data["subject"]["id"] == str(subject_id)
    assert data["brain_region"]["id"] == brain_region_id
    assert data["license"]["id"] == str(license_id)
    assert data["authorized_project_id"] == str(PROJECT_ID)


def test_read_one(client, subject_id, license_id, brain_region_id, trace_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{trace_id}",
    ).json()
    assert data["name"] == "my-name"
    assert data["description"] == "my-description"
    assert data["brain_region"]["id"] == brain_region_id
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["subject"]["id"] == str(subject_id)
    assert data["license"]["id"] == str(license_id)
    assert data["authorized_project_id"] == PROJECT_ID


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(db, client, subject_id, brain_region_id, license_id):
    _ = [
        _create_electrical_cell_recording_id(
            db,
            name=f"entity-{i}",
            subject_id=subject_id,
            brain_region_id=brain_region_id,
            license_id=license_id,
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
def faceted_ids(db, client_admin, subject_id, license_id):
    brain_region_ids = [
        create_brain_region_id(client_admin, id_=i, name=f"region-{i}") for i in range(2)
    ]

    trace_ids = [
        _create_electrical_cell_recording_id(
            db,
            name=f"trace-{i}",
            description=f"brain-region-{region_id}",
            subject_id=subject_id,
            license_id=license_id,
            brain_region_id=region_id,
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
        {"id": brain_region_ids[0], "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": brain_region_ids[1], "label": "region-1", "count": 1, "type": "brain_region"},
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"search": f"brain-region-{brain_region_ids[0]}", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["brain_region"] == [
        {"id": 0, "label": "region-0", "count": 1, "type": "brain_region"},
    ]
