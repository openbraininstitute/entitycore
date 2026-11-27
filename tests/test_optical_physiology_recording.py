from unittest.mock import ANY

import pytest

from app.db.model import OpticalPhysiologyRecording
from app.db.types import AssetLabel, EntityType, ImagingModality, OpticalRecordingOrigin

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_admin_create_one,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    create_brain_region,
    upload_entity_asset,
)

ROUTE = "/optical-physiology-recording"
ADMIN_ROUTE = f"/admin{ROUTE}"


def _create_id(client, json_data):
    return assert_request(client.post, url=ROUTE, json=json_data).json()["id"]


@pytest.fixture
def json_data(optical_physiology_recording_json_data):
    return optical_physiology_recording_json_data


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
        "id": ANY,
        "imaging_modality": "widefield",
        "license": ANY,
        "lifecycle_status": "active",
        "name": "my-name",
        "notice_text": None,
        "published_in": None,
        "recording_origin": "in_vitro",
        "sampling_frequency": 9.0,
        "subject": ANY,
        "type": EntityType.optical_physiology_recording,
        "update_date": ANY,
        "updated_by": ANY,
    }

    db_model = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    assert db_model == data


def test_admin_create_one(db, clients, json_data, mock_virtual_lab_api):
    check_admin_create_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        mock_virtual_lab_api=mock_virtual_lab_api,
    )


@pytest.mark.parametrize("field", ["sampling_frequency", "duration"])
def test_create_one_accepts_zero(client, json_data, field):
    data = assert_request(client.post, url=ROUTE, json=json_data | {field: 0}).json()
    assert data[field] == 0


@pytest.mark.parametrize("field", ["sampling_frequency", "duration"])
def test_create_one_rejects_negative_values(client, json_data, field):
    assert_request(client.post, url=ROUTE, json=json_data | {field: -1}, expected_status_code=422)


@pytest.mark.parametrize("field", ["imaging_modality", "recording_origin"])
def test_create_one_requires_field(client, json_data, field):
    json_data = {k: v for k, v in json_data.items() if k != field}
    assert_request(client.post, url=ROUTE, json=json_data, expected_status_code=422)


@pytest.mark.parametrize("field", ["imaging_modality", "recording_origin"])
def test_create_one_rejects_invalid_enum(client, json_data, field):
    assert_request(
        client.post, url=ROUTE, json=json_data | {field: "invalid"}, expected_status_code=422
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
            "duration": 900.0,
            "imaging_modality": "two_photon",
            "recording_origin": "in_vivo",
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


def test_update_brain_region(db, client, json_data, brain_region_hierarchy_id, user_id):
    entity_id = _create_id(client, json_data)
    other_region = create_brain_region(
        db, brain_region_hierarchy_id, annotation_value=99, name="other", created_by_id=user_id
    )
    url = f"{ROUTE}/{entity_id}"

    data = assert_request(
        client.patch, url=url, json={"brain_region_id": str(other_region.id)}
    ).json()
    assert data["brain_region"]["id"] == str(other_region.id)
    assert assert_request(client.get, url=url).json() == data


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={OpticalPhysiologyRecording: 1},
        expected_counts_after={OpticalPhysiologyRecording: 0},
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
        return db.get(OpticalPhysiologyRecording, entity_id)

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_upload_nwb(client, json_data):
    entity_id = _create_id(client, json_data)
    data = upload_entity_asset(
        client,
        entity_type=EntityType.optical_physiology_recording,
        entity_id=entity_id,
        files={"file": ("recording.nwb", b"nwb", "application/nwb")},
        label=AssetLabel.nwb,
    ).json()
    assert data["label"] == AssetLabel.nwb
    assert data["content_type"] == "application/nwb"


@pytest.fixture
def models(db, json_data, user_id):
    values = [
        (9.0, 600.0, ImagingModality.widefield, OpticalRecordingOrigin.in_vitro),
        (30.0, 1200.0, ImagingModality.two_photon, OpticalRecordingOrigin.in_vivo),
        (20.0, 10.0, ImagingModality.fiber_photometry, OpticalRecordingOrigin.in_vivo),
    ]
    return add_all_db(
        db,
        [
            OpticalPhysiologyRecording(
                **json_data
                | {
                    "name": f"recording-{i}",
                    "sampling_frequency": sampling_frequency,
                    "duration": duration,
                    "imaging_modality": imaging_modality,
                    "recording_origin": recording_origin,
                    "created_by_id": user_id,
                    "updated_by_id": user_id,
                    "authorized_project_id": PROJECT_ID,
                }
            )
            for i, (sampling_frequency, duration, imaging_modality, recording_origin) in enumerate(
                values
            )
        ],
    )


def test_filtering_and_sorting(client, models):
    def names(params):
        data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
        return [d["name"] for d in data]

    assert len(names({})) == len(models)
    assert names({"sampling_frequency__gte": 15.0, "order_by": "duration"}) == [
        "recording-2",
        "recording-1",
    ]
    assert names({"sampling_frequency__lte": 15.0}) == ["recording-0"]
    assert names({"duration__gte": 600.0, "duration__lte": 900.0}) == ["recording-0"]
    assert names({"order_by": "-duration"}) == ["recording-1", "recording-0", "recording-2"]
    assert names({"ilike_search": "recording-1"}) == ["recording-1"]
    assert names({"imaging_modality": "two_photon"}) == ["recording-1"]
    assert names(
        {"imaging_modality__in": ["widefield", "fiber_photometry"], "order_by": "name"}
    ) == ["recording-0", "recording-2"]
    assert names({"recording_origin": "in_vitro"}) == ["recording-0"]
    assert names({"recording_origin__in": ["in_vivo", "in_silico"], "order_by": "name"}) == [
        "recording-1",
        "recording-2",
    ]
    assert names({"order_by": "imaging_modality"}) == [
        "recording-0",
        "recording-1",
        "recording-2",
    ]
