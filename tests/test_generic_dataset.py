from datetime import timedelta
from unittest.mock import ANY

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.model import GenericDataset, Subject
from app.db.types import AssetLabel, EntityType

from .utils import (
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_update_one,
    check_missing,
    check_pagination,
    check_private_only_authorization,
    upload_entity_asset,
)

ROUTE = "/generic-dataset"
ADMIN_ROUTE = f"/admin{ROUTE}"


@pytest.fixture
def json_data(generic_dataset_json_data):
    return generic_dataset_json_data


@pytest.fixture
def full_json_data(json_data, subject_id, brain_region_id, license_id):
    return json_data | {
        "subject_id": str(subject_id),
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def test_create_one(client, user_id, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()

    assert data["created_by"]["id"] == str(user_id)
    assert data == {
        "assets": [],
        "authorized_project_id": PROJECT_ID,
        "authorized_public": False,
        "brain_region": None,
        "contributions": [],
        "created_by": ANY,
        "creation_date": ANY,
        "description": "my-description",
        "id": ANY,
        "license": None,
        "lifecycle_status": "active",
        "name": "my-dataset",
        "subject": None,
        "type": EntityType.generic_dataset,
        "update_date": ANY,
        "updated_by": ANY,
    }

    assert assert_request(client.get, url=f"{ROUTE}/{data['id']}").json() == data


def test_create_one_with_all_fields(client, full_json_data, species_id, strain_id):
    data = assert_request(client.post, url=ROUTE, json=full_json_data).json()

    assert data["subject"]["id"] == full_json_data["subject_id"]
    assert data["subject"]["species"]["id"] == str(species_id)
    assert data["subject"]["strain"]["id"] == str(strain_id)
    assert data["brain_region"]["id"] == full_json_data["brain_region_id"]
    assert data["license"]["id"] == full_json_data["license_id"]

    assert assert_request(client.get, url=f"{ROUTE}/{data['id']}").json() == data


def test_public_is_rejected_by_the_db(db, json_data, user_id):
    with pytest.raises(IntegrityError, match="ck_entity_private_only_types"):
        add_db(
            db,
            GenericDataset(
                **json_data
                | {
                    "authorized_public": True,
                    "authorized_project_id": PROJECT_ID,
                    "created_by_id": user_id,
                    "updated_by_id": user_id,
                }
            ),
        )


def test_create_one_with_private_subject(db, client, json_data, species_id, user_id):
    def add_subject(project_id):
        return add_db(
            db,
            Subject(
                name="private-subject",
                description="private-description",
                species_id=species_id,
                age_value=timedelta(days=14),
                age_period="postnatal",
                sex="female",
                authorized_public=False,
                authorized_project_id=project_id,
                created_by_id=user_id,
                updated_by_id=user_id,
            ),
        )

    # a private subject in the same project can be referenced
    subject = add_subject(PROJECT_ID)
    assert_request(client.post, url=ROUTE, json=json_data | {"subject_id": str(subject.id)})

    # a private subject in another project cannot be referenced
    subject = add_subject(UNRELATED_PROJECT_ID)
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"subject_id": str(subject.id)},
        expected_status_code=403,
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
        optional_payload=None,
        private_only=True,
    )


def test_update_optional_references(client, json_data, full_json_data):
    entity_id = assert_request(client.post, url=ROUTE, json=json_data).json()["id"]
    url = f"{ROUTE}/{entity_id}"
    references = ["subject", "brain_region", "license"]

    # the response of the PATCH returns the updated relationships
    payload = {f"{key}_id": full_json_data[f"{key}_id"] for key in references}
    data = assert_request(client.patch, url=url, json=payload).json()
    for key in references:
        assert data[key]["id"] == full_json_data[f"{key}_id"]
    assert assert_request(client.get, url=url).json() == data

    payload = {f"{key}_id": None for key in references}
    data = assert_request(client.patch, url=url, json=payload).json()
    for key in references:
        assert data[key] is None
    assert assert_request(client.get, url=url).json() == data


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={GenericDataset: 1},
        expected_counts_after={GenericDataset: 0},
        private_only=True,
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_read_many_and_authorization(clients, json_data):
    check_private_only_authorization(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_brain_region_filter(db, client, brain_region_hierarchy_id, create_id):
    def create_model_function(_db, name, brain_region_id):
        return db.get(GenericDataset, create_id(name=name, brain_region_id=str(brain_region_id)))

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


@pytest.fixture
def models(db, json_data, full_json_data, user_id):
    common = {
        "created_by_id": user_id,
        "updated_by_id": user_id,
        "authorized_project_id": PROJECT_ID,
    }
    return add_all_db(
        db,
        [
            GenericDataset(**full_json_data | common | {"name": "dataset-with-metadata"}),
            GenericDataset(**json_data | common | {"name": "dataset-without-metadata"}),
        ],
    )


def test_filtering_sorting_and_facets(client, models, full_json_data, species_id):
    def get(params):
        return assert_request(client.get, url=ROUTE, params=params).json()

    def names(params):
        return [d["name"] for d in get(params)["data"]]

    assert len(models) == 2

    # the datasets without brain region or subject are kept when sorting by them
    assert names({"order_by": "brain_region__name"}) == [
        "dataset-with-metadata",
        "dataset-without-metadata",
    ]
    assert names({"order_by": "subject__species__name"}) == [
        "dataset-with-metadata",
        "dataset-without-metadata",
    ]

    # and excluded when filtering by them
    assert names({"brain_region__id": full_json_data["brain_region_id"]}) == [
        "dataset-with-metadata"
    ]
    assert names({"subject__species__id": str(species_id)}) == ["dataset-with-metadata"]
    assert names({"ilike_search": "*without*"}) == ["dataset-without-metadata"]

    # the facets count only the datasets with a value
    facets = get({"with_facets": True})["facets"]
    assert facets["brain_region"] == [
        {"id": full_json_data["brain_region_id"], "label": ANY, "count": 1, "type": "brain_region"}
    ]
    assert facets["species"] == [
        {"id": str(species_id), "label": ANY, "count": 1, "type": "subject.species"}
    ]


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [("README.md", "text/markdown"), ("README.txt", "text/plain")],
)
def test_upload_readme(client, create_id, filename, content_type):
    data = upload_entity_asset(
        client,
        entity_type=EntityType.generic_dataset,
        entity_id=create_id(),
        files={"file": (filename, b"# My dataset", content_type)},
        label=AssetLabel.generic_dataset_readme,
    ).json()
    assert data["label"] == AssetLabel.generic_dataset_readme
    assert data["content_type"] == content_type


def test_upload_readme_with_invalid_content_type(client, create_id):
    response = upload_entity_asset(
        client,
        entity_type=EntityType.generic_dataset,
        entity_id=create_id(),
        files={"file": ("README.json", b"{}", "application/json")},
        label=AssetLabel.generic_dataset_readme,
        expected_status=422,
    )
    assert response.json()["error_code"] == "ASSET_INVALID_SCHEMA"


def test_upload_files_directory(client, create_id):
    data = assert_request(
        client.post,
        url=f"{ROUTE}/{create_id()}/assets/directory/upload",
        json={
            "files": ["raw/recording.bin", "metadata.json"],
            "meta": None,
            "label": AssetLabel.generic_dataset_files,
            "directory_name": "files",
        },
    ).json()
    assert data["asset"]["is_directory"] is True
    assert data["asset"]["label"] == AssetLabel.generic_dataset_files
    assert set(data["files"]) == {"raw/recording.bin", "metadata.json"}
