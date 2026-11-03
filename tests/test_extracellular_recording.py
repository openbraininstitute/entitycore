from unittest.mock import ANY

import pytest

from app.db.model import ExtracellularRecording
from app.db.types import AssetLabel, ElectricalRecordingOrigin, EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    upload_entity_asset,
)

ROUTE = "/extracellular-recording"
ADMIN_ROUTE = f"/admin{ROUTE}"


def _create_id(client, json_data):
    return assert_request(client.post, url=ROUTE, json=json_data).json()["id"]


def test_create_one(client, subject_id, license_id, brain_region_id, user_id, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()

    assert data["subject"]["id"] == str(subject_id)
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["license"]["id"] == str(license_id)
    assert data["created_by"]["id"] == str(user_id)
    assert data == {
        "assets": [],
        "authorized_project_id": PROJECT_ID,
        "authorized_public": False,
        "brain_region": ANY,
        "contact_email": None,
        "contributions": [],
        "created_by": ANY,
        "creation_date": ANY,
        "description": "my-description",
        "duration": 600.0,
        "experiment_date": None,
        "generated_from_derivations": None,
        "id": ANY,
        "license": ANY,
        "lifecycle_status": "active",
        "name": "my-name",
        "notice_text": None,
        "published_in": None,
        "recording_origin": ElectricalRecordingOrigin.in_vivo,
        "sampling_frequency": 30000.0,
        "subject": ANY,
        "type": EntityType.extracellular_recording,
        "update_date": ANY,
        "updated_by": ANY,
        "used_by_derivations": None,
    }

    db_model = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    assert db_model == data


@pytest.fixture
def json_data(extracellular_recording_json_data):
    return extracellular_recording_json_data


@pytest.mark.parametrize("field", ["sampling_frequency", "duration"])
def test_create_one_rejects_non_positive_values(client, json_data, field):
    assert_request(client.post, url=ROUTE, json=json_data | {field: 0}, expected_status_code=422)


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
            "duration": 900.0,
        },
        optional_payload={
            "contact_email": "lab@example.org",
        },
    )


def test_read_many(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={ExtracellularRecording: 1},
        expected_counts_after={ExtracellularRecording: 0},
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_brain_region_filter(db, client, brain_region_hierarchy_id, json_data):
    def create_model_function(_db, name, brain_region_id):
        entity_id = _create_id(
            client, json_data | {"name": name, "brain_region_id": str(brain_region_id)}
        )
        return db.get(ExtracellularRecording, entity_id)

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_upload_nwb(client, json_data):
    entity_id = _create_id(client, json_data)
    data = upload_entity_asset(
        client,
        entity_type=EntityType.extracellular_recording,
        entity_id=entity_id,
        files={"file": ("recording.nwb", b"nwb", "application/nwb")},
        label=AssetLabel.nwb,
    ).json()
    assert data["label"] == AssetLabel.nwb
    assert data["content_type"] == "application/nwb"


@pytest.fixture
def models(db, json_data, user_id):
    values = [
        (ElectricalRecordingOrigin.in_vivo, 30000.0, 600.0),
        (ElectricalRecordingOrigin.in_vivo, 30000.0, 1200.0),
        (ElectricalRecordingOrigin.in_silico, 20000.0, 10.0),
    ]
    return add_all_db(
        db,
        [
            ExtracellularRecording(
                **json_data
                | {
                    "name": f"recording-{i}",
                    "recording_origin": origin,
                    "sampling_frequency": sampling_frequency,
                    "duration": duration,
                    "created_by_id": user_id,
                    "updated_by_id": user_id,
                    "authorized_project_id": PROJECT_ID,
                }
            )
            for i, (origin, sampling_frequency, duration) in enumerate(values)
        ],
    )


def test_filtering_and_sorting(client, models):
    def names(params):
        data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
        return [d["name"] for d in data]

    assert len(names({})) == len(models)
    assert names({"recording_origin": "in_silico"}) == ["recording-2"]
    assert names({"sampling_frequency__gte": 25000.0, "order_by": "duration"}) == [
        "recording-0",
        "recording-1",
    ]
    assert names({"sampling_frequency__lte": 25000.0}) == ["recording-2"]
    assert names({"duration__gte": 600.0, "duration__lte": 900.0}) == ["recording-0"]
    assert names({"order_by": "-duration"}) == ["recording-1", "recording-0", "recording-2"]
    assert names({"ilike_search": "recording-1"}) == ["recording-1"]
