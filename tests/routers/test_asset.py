import io
from unittest.mock import ANY, patch

import pytest
from moto import mock_aws

from app.config import storages
from app.db.model import Asset, Entity
from app.db.types import AssetLabel, AssetStatus, EntityType, StorageType
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse
from app.schemas.asset import AssetRead
from app.utils.s3 import build_s3_path

from tests.conftest import assert_request
from tests.utils import (
    MISSING_ID,
    PROJECT_ID,
    TEST_DATA_DIR,
    VIRTUAL_LAB_ID,
    add_db,
    create_cell_morphology_id,
    route,
    upload_entity_asset,
)

DIFFERENT_ENTITY_TYPE = "experimental_bouton_density"

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
FILE_EXAMPLE_DIGEST = "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91"
FILE_EXAMPLE_SIZE = 31


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
def entity(client, subject_id, brain_region_id) -> Entity:
    entity_type = EntityType.cell_morphology
    entity_id = create_cell_morphology_id(
        client,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    return Entity(id=entity_id, type=entity_type)


def _upload_entity_asset(
    client, entity_type, entity_id, label, file_upload_name, content_type, expected_status=None
):
    with FILE_EXAMPLE_PATH.open("rb") as f:
        files = {
            # (filename, file (or bytes), content_type, headers)
            "file": (file_upload_name, f, content_type)
        }
        return upload_entity_asset(
            client=client,
            entity_type=entity_type,
            entity_id=entity_id,
            files=files,
            label=label,
            expected_status=expected_status,
        )


@pytest.fixture
def asset(client, entity) -> AssetRead:
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    return AssetRead.model_validate(data)


@pytest.fixture
def asset_directory(db, root_circuit, person_id) -> Asset:
    s3_path = _get_expected_full_path(entity=root_circuit, path="my-directory")
    asset = Asset(
        path="my-directory",
        full_path=s3_path,
        status="created",
        is_directory=True,
        content_type="application/vnd.directory",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=root_circuit.id,
        created_by_id=person_id,
        updated_by_id=person_id,
        label="sonata_circuit",
        storage_type=StorageType.aws_s3_internal,
    )
    add_db(db, asset)
    return asset


def test_upload_entity_asset(client, entity):
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()

    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
    assert data == {
        "id": ANY,
        "path": "morph.asc",
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "application/asc",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
        "meta": {},
        "status": "created",
        "label": "morphology",
        "storage_type": StorageType.aws_s3_internal,
    }

    # try to upload again the same file with the same path
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 409, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED

    # try to upload to a non-existent entity id
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=MISSING_ID,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to upload to valid entity id, but different entity type
    response = _upload_entity_asset(
        client,
        entity_type=EntityType[DIFFERENT_ENTITY_TYPE],
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 404, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to upload a file w/ a full path
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        file_upload_name="a/b/c.asc",
        label="morphology",
        content_type="application/asc",
    )
    assert response.status_code == 422, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_PATH

    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="foo.obj",
        content_type="application/octet-stream",
    )
    assert response.status_code == 422, f"Asset creation didn't fail as expected: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_CONTENT_TYPE


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_upload_entity_asset_non_authorized(
    request, client_fixture, expected_status, expected_error, entity
):
    client = request.getfixturevalue(client_fixture)

    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == expected_status, (
        f"Asset creation didn't fail as expected: {response.text}"
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == expected_error


def test_upload_entity_asset__label(monkeypatch, client, entity):
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="foo",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 422, "Assel label was not rejected as not present in AssetLabel."

    monkeypatch.setattr("app.schemas.asset.ALLOWED_ASSET_LABELS_PER_ENTITY", {})

    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 422
    assert response.json() == {
        "error_code": "ASSET_INVALID_SCHEMA",
        "message": "Asset schema is invalid",
        "details": [f"Value error, There are no allowed asset labels defined for '{entity.type}'"],
    }

    required = {EntityType.cell_morphology: {AssetLabel.cell_composition_summary: None}}

    monkeypatch.setattr("app.schemas.asset.ALLOWED_ASSET_LABELS_PER_ENTITY", required)

    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 422
    assert response.json() == {
        "error_code": "ASSET_INVALID_SCHEMA",
        "message": "Asset schema is invalid",
        "details": [
            f"Value error, Asset label '{AssetLabel.morphology}' is not allowed for "
            f"entity type '{entity.type}'. "
            f"Allowed asset labels: ['{AssetLabel.cell_composition_summary}']"
        ],
    }


@pytest.fixture
def s3_file(s3):
    storage_type = StorageType.aws_s3_open
    bucket = storages[storage_type].bucket
    key = "path/to/test.swc"
    file_obj = io.BytesIO(b"test")
    s3.upload_fileobj(file_obj, Bucket=bucket, Key=key)
    yield
    s3.delete_object(Bucket=bucket, Key=key)


@pytest.mark.usefixtures("s3_file")
def test_register_entity_asset_as_file(client, entity):
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/register",
        json={
            "path": "my-test-file.swc",
            "full_path": "path/to/test.swc",
            "is_directory": False,
            "content_type": "application/swc",
            "label": "morphology",
            "storage_type": "aws_s3_open",
        },
        expected_status_code=201,
    )
    assert response.json() == {
        "id": ANY,
        "path": "my-test-file.swc",
        "full_path": "path/to/test.swc",
        "is_directory": False,
        "content_type": "application/swc",
        "label": "morphology",
        "meta": {},
        "sha256_digest": None,
        "size": -1,
        "status": "created",
        "storage_type": "aws_s3_open",
    }


@pytest.mark.usefixtures("s3_file")
def test_register_entity_asset_as_directory(client, circuit):
    response = assert_request(
        client.post,
        url=f"{route(circuit.type)}/{circuit.id}/assets/register",
        json={
            "path": "my-test-dir",
            "full_path": "path/to",
            "is_directory": True,
            "content_type": "application/vnd.directory",
            "label": "sonata_circuit",
            "storage_type": "aws_s3_open",
        },
        expected_status_code=201,
    )
    assert response.json() == {
        "id": ANY,
        "path": "my-test-dir",
        "full_path": "path/to",
        "is_directory": True,
        "content_type": "application/vnd.directory",
        "label": "sonata_circuit",
        "meta": {},
        "sha256_digest": None,
        "size": -1,
        "status": "created",
        "storage_type": "aws_s3_open",
    }


def test_register_entity_asset_not_found(client, entity):
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/register",
        json={
            "path": "my-test.swc",
            "full_path": "path/to/test.swc",
            "is_directory": False,
            "content_type": "application/swc",
            "label": "morphology",
            "storage_type": "aws_s3_open",
        },
        expected_status_code=409,
    )
    assert response.json() == {
        "details": {
            "bucket": "openbluebrain",
            "region": "us-west-2",
            "s3_key": "path/to/test.swc",
        },
        "error_code": "ASSET_NOT_FOUND",
        "message": "Object does not exist in S3",
    }


@pytest.mark.parametrize(
    "full_path",
    [
        "/path/to/test.swc",
        "path/to/test.swc/",
        "/path/to/test.swc/",
        "/path/to//test.swc",
        "/path/to/./test.swc",
        "/path/to/../test.swc",
    ],
)
def test_register_entity_asset_with_invalid_full_path(client, entity, full_path):
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/register",
        json={
            "path": "my-test.swc",
            "full_path": full_path,
            "is_directory": False,
            "content_type": "application/swc",
            "label": "morphology",
            "storage_type": "aws_s3_open",
        },
        expected_status_code=422,
    )
    assert response.json() == {
        "details": ANY,
        "error_code": "INVALID_REQUEST",
        "message": "Validation error",
    }
    assert response.json()["details"][0]["msg"] == (
        "Value error, Invalid full path: cannot be empty, start or end with '/', "
        "and the path components cannot be empty, '.' or '..'"
    )


@pytest.mark.parametrize(
    ("storage_type", "err_msg"),
    [
        (
            StorageType.aws_s3_internal,
            "Value error, Only open data storage is supported for registration",
        ),
        ("invalid_storage_type", "Input should be 'aws_s3_internal' or 'aws_s3_open'"),
    ],
)
def test_register_entity_asset_with_invalid_storage_type(client, entity, storage_type, err_msg):
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/register",
        json={
            "path": "my-test.swc",
            "full_path": "path/to/test.swc",
            "is_directory": False,
            "content_type": "application/swc",
            "label": "morphology",
            "storage_type": storage_type,
        },
        expected_status_code=422,
    )
    assert response.json() == {
        "details": ANY,
        "error_code": "INVALID_REQUEST",
        "message": "Validation error",
    }
    assert response.json()["details"][0]["msg"] == err_msg


def test_get_entity_asset(client, entity, asset):
    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()
    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
    assert data == {
        "id": str(asset.id),
        "path": "morph.asc",
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "application/asc",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
        "meta": {},
        "status": "created",
        "label": "morphology",
        "storage_type": StorageType.aws_s3_internal,
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


@pytest.mark.parametrize("client_fixture", ["client_user_2", "client_no_project"])
def test_get_entity_asset_non_authorized(request, client_fixture, entity, asset):
    client = request.getfixturevalue(client_fixture)

    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_get_entity_assets(client, entity, asset):
    response = client.get(f"{route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]
    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
    assert data == [
        {
            "id": str(asset.id),
            "path": "morph.asc",
            "full_path": expected_full_path,
            "is_directory": False,
            "content_type": "application/asc",
            "size": FILE_EXAMPLE_SIZE,
            "sha256_digest": FILE_EXAMPLE_DIGEST,
            "meta": {},
            "status": "created",
            "label": "morphology",
            "storage_type": StorageType.aws_s3_internal,
        }
    ]

    # try to get assets with non-existent entity id
    response = client.get(f"{route(entity.type)}/{MISSING_ID}/assets")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_get_deleted_entity_assets__admin(client, client_admin, entity, asset):
    """Test that a service admin can fetch marked as deleted assets."""

    response = client_admin.get(f"/admin{route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]

    expected_full_path = _get_expected_full_path(entity, path="morph.asc")

    expected_asset_payload = {
        "id": str(asset.id),
        "path": "morph.asc",
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "application/asc",
        "size": FILE_EXAMPLE_SIZE,
        "sha256_digest": FILE_EXAMPLE_DIGEST,
        "meta": {},
        "status": "created",
        "label": "morphology",
        "storage_type": StorageType.aws_s3_internal,
    }

    assert data == [expected_asset_payload]

    # mark as deleted, ensure that admin can get the deleted asset
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

    response = client_admin.get(f"/admin{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"
    assert response.json() == expected_asset_payload | {"status": "deleted"}

    response = client_admin.get(f"/admin{route(entity.type)}/{entity.id}/assets")
    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]

    assert data == [expected_asset_payload | {"status": "deleted"}]

    # delete completely as admin
    response = client_admin.delete(f"/admin{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

    response = client_admin.get(f"/admin{route(entity.type)}/{entity.id}/assets")
    assert response.status_code == 200, f"Failed to get asset: {response.text}"
    data = response.json()["data"]
    assert data == []


@pytest.mark.parametrize("client_fixture", ["client_user_2", "client_no_project"])
def test_get_entity_assets_non_authorized(request, client_fixture, entity):
    client = request.getfixturevalue(client_fixture)

    response = client.get(f"{route(entity.type)}/{entity.id}/assets")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_download_entity_asset(client, entity, asset):
    response = client.get(
        f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        follow_redirects=False,
    )

    assert response.status_code == 307, f"Failed to download asset: {response.text}"
    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
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


@pytest.mark.parametrize("client_fixture", ["client_user_2", "client_no_project"])
def test_download_entity_asset_non_authorized(request, client_fixture, entity, asset):
    client = request.getfixturevalue(client_fixture)

    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_delete_entity_asset(client, entity, asset):
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"
    data = response.json()
    assert data == asset.model_copy(update={"status": AssetStatus.DELETED}).model_dump(mode="json")

    # try to delete again the same asset
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND

    # try to delete an asset with non-existent entity id
    response = client.delete(f"{route(entity.type)}/{MISSING_ID}/assets/{asset.id}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to delete an asset with non-existent asset id
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_delete_entity_asset_non_authorized(
    request, client_fixture, expected_status, expected_error, entity, asset
):
    client = request.getfixturevalue(client_fixture)

    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == expected_status, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == expected_error


def test_upload_delete_upload_entity_asset(client, entity):
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset0 = AssetRead.model_validate(data)

    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset0.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

    # upload the asset with the same path
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="morph.asc",
        content_type="application/asc",
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()
    asset1 = AssetRead.model_validate(data)

    # test that the deleted assets are filtered out
    response = client.get(f"{route(entity.type)}/{entity.id}/assets")

    assert response.status_code == 200, f"Failed to get assest: {response.text}"
    data = response.json()["data"]
    assert len(data) == 1

    assert data[0]["id"] == str(asset1.id)
    assert data[0]["path"] == "morph.asc"
    assert data[0]["status"] == "created"

    # test that the assets joined in the entity metadata also not include the deleted
    response = client.get(f"{route(entity.type)}/{entity.id}")
    data = response.json()["assets"]
    assert len(data) == 1
    assert data[0]["id"] == str(asset1.id)
    assert data[0]["path"] == "morph.asc"
    assert data[0]["status"] == "created"


def test_download_directory_file(client, root_circuit, asset_directory):
    response = client.get(
        url=f"{route(root_circuit.type)}/{root_circuit.id}/assets/{asset_directory.id}/download",
        params={"asset_path": "file1.txt"},
        follow_redirects=False,
    )
    assert response.status_code == 307, f"Failed to download directory file: {response.text}"

    # asset_path is mandatory if the asset is a direcotory
    response = client.get(
        url=f"{route(root_circuit.type)}/{root_circuit.id}/assets/{asset_directory.id}/download",
        follow_redirects=False,
    )
    assert response.status_code == 409, (
        f"Failed to send invalid response due to missing asset_path: {response.text}"
    )


def test_upload_entity_asset_directory(client, root_circuit):
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id
    label = "sonata_circuit"

    files_to_upload = [
        "morphology/cell1.swc",
        "morphology/cell2.swc",
        "metadata/info.json",
        "images/preview.png",
    ]

    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={
                "files": files_to_upload,
                "meta": None,
                "label": label,
                "directory_name": "test0",
            },
        )

    assert response.status_code == 200, f"Asset creation failed: {response.text}"
    data = response.json()

    assert "asset" in data
    assert "files" in data

    asset_data = data["asset"]
    assert asset_data["is_directory"] is True
    assert asset_data["status"] == "created"
    assert asset_data["label"] == label
    assert asset_data["meta"] == {}

    urls = data["files"]
    assert len(urls) == len(files_to_upload)

    for file_path in files_to_upload:
        assert file_path in urls
        url = urls[file_path]
        assert "AWSAccessKeyId" in url
        assert "Signature" in url
        assert "Expires" in url
        assert url.startswith("https://")

    # duplicate `directory_name`
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={
                "files": files_to_upload,
                "meta": None,
                "label": label,
                "directory_name": "test0",
            },
        )
    assert response.status_code == 409
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED

    with mock_aws():
        response = client.post(
            f"{entity_type}/{MISSING_ID}/assets/directory/upload",
            json={
                "files": files_to_upload,
                "meta": None,
                "label": label,
                "directory_name": "test1",
            },
        )
    assert response.status_code == 404
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # Try to upload empty directory
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={"files": [], "meta": None, "label": label, "directory_name": "test2"},
        )
        assert response.status_code == 422

    duplicate_path = ["../../../etc/passwd", "valid/path/../../../etc/passwd"]
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={"files": duplicate_path, "meta": None, "label": label, "directory_name": "test3"},
        )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_PATH

    invalid_files = [
        "/absolute/path/file.txt",
        "../../../etc/passwd",
        "valid/path/../../../etc/groups",
    ]
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={"files": invalid_files, "meta": None, "label": label, "directory_name": "test4"},
        )
    assert response.status_code == 200
    assert list(response.json()["files"]) == [
        "absolute/path/file.txt",
        "etc/passwd",
        "etc/groups",
    ]


def test_list_entity_asset_directory(client, root_circuit, asset_directory):
    entity_id = root_circuit.id
    entity_type = route(root_circuit.type)

    with patch("app.service.asset.list_directory_with_details") as mock_list_directory:
        fake_files = {
            "morphology/cell1.swc": {
                "name": "morphology/cell1.swc",
                "size": 12345,
                "last_modified": "2024-01-15T10:30:00Z",
            },
            "morphology/cell2.swc": {
                "name": "morphology/cell2.swc",
                "size": 23456,
                "last_modified": "2024-01-15T10:35:00Z",
            },
            "metadata/info.json": {
                "name": "metadata/info.json",
                "size": 1024,
                "last_modified": "2024-01-15T10:40:00Z",
            },
        }
        mock_list_directory.return_value = fake_files

        response = client.get(f"{entity_type}/{entity_id}/assets/{asset_directory.id}/list")

    assert response.status_code == 200
    data = response.json()

    assert "files" in data
    assert data["files"] == fake_files


def test_list_entity_asset_directory_failures(client, entity, asset):
    entity_type = route(entity.type)
    # non-directory asset
    response = client.get(f"{entity_type}/{entity.id}/assets/{asset.id}/list")
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_A_DIRECTORY

    # non-existent entity
    response = client.get(f"{entity_type}/{MISSING_ID}/assets/{MISSING_ID}/list")
    assert response.status_code == 404
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # non-existent asset
    response = client.get(f"{entity_type}/{entity.id}/assets/{MISSING_ID}/list")
    assert response.status_code == 404
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_list_entity_asset_directory_non_authorized(
    request, client_fixture, expected_status, expected_error, entity, asset
):
    client = request.getfixturevalue(client_fixture)
    entity_type = route(entity.type)

    response = client.get(f"{entity_type}/{entity.id}/assets/{asset.id}/list")
    assert response.status_code == expected_status
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == expected_error
