from unittest.mock import ANY

import pytest

from app.db.model import Entity
from app.db.types import AssetStatus, EntityWithAssets
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse
from app.schemas.asset import AssetRead

from tests.utils import (
    PROJECT_HEADERS,
    PROJECT_ID,
    TEST_DATA_DIR,
    VIRTUAL_LAB_ID,
    create_reconstruction_morphology_id,
)

NON_EXISTENT_ID = 999999999
DIFFERENT_ENTITY_TYPE = "experimental_bouton_density"

# Apply the fixture to all tests in this module
pytestmark = pytest.mark.usefixtures("skip_project_check")


@pytest.fixture
def client(client):
    client.headers.update(PROJECT_HEADERS)
    return client


def _route(entity_type: str) -> str:
    return f"/{EntityWithAssets[entity_type]}"


def _upload_entity_asset(client, entity_type, entity_id):
    with (TEST_DATA_DIR / "example.json").open("rb") as f:
        files = {
            # (filename, file (or bytes), content_type, headers)
            "file": ("a/b/c.txt", f, "text/plain")
        }
        return client.post(f"{_route(entity_type)}/{entity_id}/assets", files=files)


def _get_expected_fullpath(entity, path):
    entity_id_mod = f"{entity.id % 0xFFFF:04x}"
    return (
        f"private/{VIRTUAL_LAB_ID[:4]}/{VIRTUAL_LAB_ID}/{PROJECT_ID}/"
        f"assets/{entity.type}/{entity_id_mod}/{entity.id}/{path}"
    )


@pytest.fixture
def entity(client, species_id, strain_id, brain_region_id) -> Entity:
    entity_type = EntityWithAssets.reconstruction_morphology.name
    entity_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=PROJECT_HEADERS,
        authorized_public=False,
    )
    return Entity(id=entity_id, type=entity_type)


@pytest.fixture
def asset(client, entity) -> AssetRead:
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    return AssetRead.model_validate(data)


def test_upload_entity_asset(client, entity):
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()

    expected_fullpath = _get_expected_fullpath(entity, path="a/b/c.txt")
    assert data == {
        "id": ANY,
        "path": "a/b/c.txt",
        "fullpath": expected_fullpath,
        "bucket_name": "obi-private",
        "is_directory": False,
        "content_type": "text/plain",
        "size": 31,
        "meta": {},
        "status": "created",
    }

    # try to upload again the same file with the same path
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 409, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED

    # try to upload to a non-existent entity id
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=NON_EXISTENT_ID)
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to upload to valid entity id, but different entity type
    response = _upload_entity_asset(client, entity_type=DIFFERENT_ENTITY_TYPE, entity_id=entity.id)
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_get_entity_asset(client, entity, asset):
    response = client.get(f"{_route(entity.type)}/{entity.id}/assets/{asset.id}")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()
    expected_fullpath = _get_expected_fullpath(entity, path="a/b/c.txt")
    assert data == {
        "id": asset.id,
        "path": "a/b/c.txt",
        "fullpath": expected_fullpath,
        "bucket_name": "obi-private",
        "is_directory": False,
        "content_type": "text/plain",
        "size": 31,
        "meta": {},
        "status": "created",
    }

    # try to get an asset with non-existent entity id
    response = client.get(f"{_route(entity.type)}/{NON_EXISTENT_ID}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to get an asset with non-existent asset id
    response = client.get(f"{_route(entity.type)}/{entity.id}/assets/{NON_EXISTENT_ID}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


def test_get_entity_assets(client, entity, asset):
    response = client.get(f"{_route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]
    expected_fullpath = _get_expected_fullpath(entity, path="a/b/c.txt")
    assert data == [
        {
            "id": asset.id,
            "path": "a/b/c.txt",
            "fullpath": expected_fullpath,
            "bucket_name": "obi-private",
            "is_directory": False,
            "content_type": "text/plain",
            "size": 31,
            "meta": {},
            "status": "created",
        }
    ]

    # try to get assets with non-existent entity id
    response = client.get(f"{_route(entity.type)}/{NON_EXISTENT_ID}/assets")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_download_entity_asset(client, entity, asset):
    response = client.get(
        f"{_route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        follow_redirects=False,
    )

    assert response.status_code == 307, f"Failed to download asset: {response.text}"
    expected_fullpath = _get_expected_fullpath(entity, path="a/b/c.txt")
    expected_params = {"AWSAccessKeyId", "Signature", "Expires"}
    assert response.next_request.url.path.endswith(expected_fullpath)
    assert expected_params.issubset(response.next_request.url.params)

    # try to download an asset with non-existent entity id
    response = client.get(f"{_route(entity.type)}/{NON_EXISTENT_ID}/assets/{asset.id}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to download an asset with non-existent asset id
    response = client.get(f"{_route(entity.type)}/{entity.id}/assets/{NON_EXISTENT_ID}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


def test_delete_entity_asset(client, entity, asset):
    response = client.delete(f"{_route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"
    data = response.json()
    assert data == asset.model_copy(update={"status": AssetStatus.DELETED}).model_dump(mode="json")

    # try to delete again the same asset
    response = client.delete(f"{_route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"

    # try to delete an asset with non-existent entity id
    response = client.delete(f"{_route(entity.type)}/{NON_EXISTENT_ID}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"

    # try to delete an asset with non-existent asset id
    response = client.delete(f"{_route(entity.type)}/{entity.id}/assets/{NON_EXISTENT_ID}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"


def test_upload_delete_upload_entity_asset(client, entity):
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset0 = AssetRead.model_validate(data)

    response = client.delete(f"{_route(entity.type)}/{entity.id}/assets/{asset0.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

    # upload the asset with the same path
    response = _upload_entity_asset(client, entity_type=entity.type, entity_id=entity.id)
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset1 = AssetRead.model_validate(data)

    response = client.get(f"{_route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get assest: {response.text}"
    data = response.json()["data"]
    assert len(data) == 2

    assert data[0]["id"] == asset0.id
    assert data[0]["path"] == "a/b/c.txt"
    assert data[0]["status"] == "deleted"

    assert data[1]["id"] == asset1.id
    assert data[1]["path"] == "a/b/c.txt"
    assert data[1]["status"] == "created"
