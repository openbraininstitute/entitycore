from unittest.mock import ANY

import pytest

from app.db.model import Asset, Entity
from app.db.types import AssetLabel, AssetStatus, EntityType
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse
from app.schemas.asset import AssetRead
from app.utils.s3 import build_s3_path

from tests.utils import (
    MISSING_ID,
    PROJECT_ID,
    TEST_DATA_DIR,
    VIRTUAL_LAB_ID,
    add_db,
    create_reconstruction_morphology_id,
    route,
    upload_entity_asset,
)

DIFFERENT_ENTITY_TYPE = "experimental_bouton_density"

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
FILE_EXAMPLE_DIGEST = "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91"
FILE_EXAMPLE_SIZE = 31
FILE_UPLOAD_NAME = "a.txt"


def _get_expected_full_path(entity, path):
    return build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType[entity.type],
        entity_id=entity.id,
        filename=path,
        is_public=False,
    )


@pytest.fixture
def entity(client, species_id, strain_id, brain_region_id) -> Entity:
    entity_type = EntityType.reconstruction_morphology
    entity_id = create_reconstruction_morphology_id(
        client,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    return Entity(id=entity_id, type=entity_type)


def _upload_entity_asset(
    client, entity_type, entity_id, label=None, file_upload_name=FILE_UPLOAD_NAME
):
    with FILE_EXAMPLE_PATH.open("rb") as f:
        files = {
            # (filename, file (or bytes), content_type, headers)
            "file": (file_upload_name, f, "text/plain")
        }
        return upload_entity_asset(
            client=client, entity_type=entity_type, entity_id=entity_id, files=files, label=label
        )


@pytest.fixture
def asset(client, entity) -> AssetRead:
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    return AssetRead.model_validate(data)


@pytest.fixture
def asset_directory(db, entity, person_id) -> AssetRead:
    s3_path = _get_expected_full_path(entity=entity, path="my-directory")
    asset = Asset(
        path="my-directory",
        full_path=s3_path,
        status="created",
        is_directory=True,
        content_type="directory/image",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=entity.id,
        created_by_id=person_id,
        updated_by_id=person_id,
    )
    add_db(db, asset)
    return asset


def test_upload_entity_asset(client, entity):
    response = _upload_entity_asset(
        client, entity_type=entity.type, entity_id=entity.id, label="neurolucida"
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()

    expected_full_path = _get_expected_full_path(entity, path=FILE_UPLOAD_NAME)
    assert data == {
        "id": ANY,
        "path": FILE_UPLOAD_NAME,
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "text/plain",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
        "meta": {},
        "status": "created",
        "label": "neurolucida",
    }

    # try to upload again the same file with the same path
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 409, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED

    # try to upload to a non-existent entity id
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=MISSING_ID)
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to upload to valid entity id, but different entity type
    response = _upload_entity_asset(
        client, entity_type=EntityType[DIFFERENT_ENTITY_TYPE], entity_id=entity.id
    )
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to upload a file w/ a full path
    response = _upload_entity_asset(
        client, entity_type=entity.type, entity_id=entity.id, file_upload_name="a/b/c.txt"
    )
    assert response.status_code == 422, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_PATH


def test_upload_entity_asset__label(monkeypatch, client, entity):
    response = _upload_entity_asset(
        client, entity_type=entity.type, entity_id=entity.id, label="foo"
    )
    assert response.status_code == 422, "Assel label was not rejected as not present in AssetLabel."

    monkeypatch.setattr("app.schemas.asset.ALLOWED_ASSET_LABELS_PER_ENTITY", {})

    response = _upload_entity_asset(
        client, entity_type=entity.type, entity_id=entity.id, label=AssetLabel.hdf5
    )
    assert response.status_code == 422
    assert response.json() == {
        "error_code": "ASSET_INVALID_SCHEMA",
        "message": "Asset schema is invalid",
        "details": [f"Value error, There are no allowed asset labels defined for '{entity.type}'"],
    }

    required = {EntityType.reconstruction_morphology: {AssetLabel.swc}}

    monkeypatch.setattr("app.schemas.asset.ALLOWED_ASSET_LABELS_PER_ENTITY", required)

    response = _upload_entity_asset(
        client, entity_type=entity.type, entity_id=entity.id, label=AssetLabel.hdf5
    )
    assert response.status_code == 422
    assert response.json() == {
        "error_code": "ASSET_INVALID_SCHEMA",
        "message": "Asset schema is invalid",
        "details": [
            f"Value error, Asset label '{AssetLabel.hdf5}' is not allowed for "
            f"entity type '{entity.type}'. Allowed asset labels: ['{AssetLabel.swc}']"
        ],
    }


def test_get_entity_asset(client, entity, asset):
    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()
    expected_full_path = _get_expected_full_path(entity, path=FILE_UPLOAD_NAME)
    assert data == {
        "id": str(asset.id),
        "path": FILE_UPLOAD_NAME,
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "text/plain",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
        "meta": {},
        "status": "created",
        "label": None,
    }

    # try to get an asset with non-existent entity id
    response = client.get(f"{route(entity.type)}/{MISSING_ID}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to get an asset with non-existent asset id
    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


def test_get_entity_assets(client, entity, asset):
    response = client.get(f"{route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]
    expected_full_path = _get_expected_full_path(entity, path=FILE_UPLOAD_NAME)
    assert data == [
        {
            "id": str(asset.id),
            "path": FILE_UPLOAD_NAME,
            "full_path": expected_full_path,
            "is_directory": False,
            "content_type": "text/plain",
            "size": FILE_EXAMPLE_SIZE,
            "sha256_digest": FILE_EXAMPLE_DIGEST,
            "meta": {},
            "status": "created",
            "label": None,
        }
    ]

    # try to get assets with non-existent entity id
    response = client.get(f"{route(entity.type)}/{MISSING_ID}/assets")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_download_entity_asset(client, entity, asset):
    response = client.get(
        f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        follow_redirects=False,
    )

    assert response.status_code == 307, f"Failed to download asset: {response.text}"
    expected_full_path = _get_expected_full_path(entity, path=FILE_UPLOAD_NAME)
    expected_params = {"AWSAccessKeyId", "Signature", "Expires"}
    assert response.next_request.url.path.endswith(expected_full_path)
    assert expected_params.issubset(response.next_request.url.params)

    # try to download an asset with non-existent entity id
    response = client.get(f"{route(entity.type)}/{MISSING_ID}/assets/{asset.id}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to download an asset with non-existent asset id
    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND

    # when downloading a single file asset_path should not be passed as a parameter
    response = client.get(
        f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        params={"asset_path": "foo"},
        follow_redirects=False,
    )
    assert response.status_code == 409, (
        f"Failed to forbid asset_path when downloading a file: {response.text}"
    )


def test_delete_entity_asset(client, entity, asset):
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"
    data = response.json()
    assert data == asset.model_copy(update={"status": AssetStatus.DELETED}).model_dump(mode="json")

    # try to delete again the same asset
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"

    # try to delete an asset with non-existent entity id
    response = client.delete(f"{route(entity.type)}/{MISSING_ID}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"

    # try to delete an asset with non-existent asset id
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"


def test_upload_delete_upload_entity_asset(client, entity):
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset0 = AssetRead.model_validate(data)

    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset0.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

    # upload the asset with the same path
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset1 = AssetRead.model_validate(data)

    # test that the deleted assets are filtered out
    response = client.get(f"{route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get assest: {response.text}"
    data = response.json()["data"]
    assert len(data) == 1

    assert data[0]["id"] == str(asset1.id)
    assert data[0]["path"] == FILE_UPLOAD_NAME
    assert data[0]["status"] == "created"


def test_download_directory_file(client, entity, asset_directory):
    response = client.get(
        url=f"{route(entity.type)}/{entity.id}/assets/{asset_directory.id}/download",
        params={"asset_path": "file1.txt"},
        follow_redirects=False,
    )
    assert response.status_code == 307, f"Failed to download directory file: {response.text}"

    # asset_path is mandatory if the asset is a direcotory
    response = client.get(
        url=f"{route(entity.type)}/{entity.id}/assets/{asset_directory.id}/download",
        follow_redirects=False,
    )
    assert response.status_code == 409, (
        f"Failed to send invalid response due to missing asset_path: {response.text}"
    )
