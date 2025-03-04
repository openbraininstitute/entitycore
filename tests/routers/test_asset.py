from unittest.mock import ANY

import pytest

from app.db.model import Entity
from app.db.types import AssetStatus, EntityType
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse
from app.schemas.asset import AssetRead
from app.utils.s3 import build_s3_path

from tests.utils import (
    PROJECT_HEADERS,
    PROJECT_ID,
    TEST_DATA_DIR,
    VIRTUAL_LAB_ID,
    create_reconstruction_morphology_id,
)

NON_EXISTENT_ID = 999999999
DIFFERENT_ENTITY_TYPE = "experimental_bouton_density"

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
FILE_EXAMPLE_DIGEST = "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91"
FILE_EXAMPLE_SIZE = 31

# Apply the fixture to all tests in this module
pytestmark = pytest.mark.usefixtures("skip_project_check")


@pytest.fixture
def client(client):
    client.headers.update(PROJECT_HEADERS)
    return client


def _route(entity_type: str) -> str:
    return f"/{EntityType[entity_type]}"


def _upload_entity_asset(client, entity_type, entity_id):
    with FILE_EXAMPLE_PATH.open("rb") as f:
        files = {
            # (filename, file (or bytes), content_type, headers)
            "file": ("a/b/c.txt", f, "text/plain")
        }
        return client.post(f"{_route(entity_type)}/{entity_id}/assets", files=files)


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
    entity_type = EntityType.reconstruction_morphology.name
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

    expected_full_path = _get_expected_full_path(entity, path="a/b/c.txt")
    assert data == {
        "id": ANY,
        "path": "a/b/c.txt",
        "full_path": expected_full_path,
        "bucket_name": "obi-private",
        "is_directory": False,
        "content_type": "text/plain",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
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
    expected_full_path = _get_expected_full_path(entity, path="a/b/c.txt")
    assert data == {
        "id": asset.id,
        "path": "a/b/c.txt",
        "full_path": expected_full_path,
        "bucket_name": "obi-private",
        "is_directory": False,
        "content_type": "text/plain",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
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
    expected_full_path = _get_expected_full_path(entity, path="a/b/c.txt")
    assert data == [
        {
            "id": asset.id,
            "path": "a/b/c.txt",
            "full_path": expected_full_path,
            "bucket_name": "obi-private",
            "is_directory": False,
            "content_type": "text/plain",
            "size": FILE_EXAMPLE_SIZE,
            "sha256_digest": FILE_EXAMPLE_DIGEST,
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
    expected_full_path = _get_expected_full_path(entity, path="a/b/c.txt")
    expected_params = {"AWSAccessKeyId", "Signature", "Expires"}
    assert response.next_request.url.path.endswith(expected_full_path)
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
