import io
from http import HTTPStatus
from unittest.mock import ANY, patch
from urllib.parse import parse_qs, urlparse

import pytest
from moto import mock_aws

from app.config import settings, storages
from app.db.model import Asset, Entity
from app.db.types import AssetLabel, EntityType, StorageType
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse
from app.schemas.asset import AssetRead, MultipartDirectoryUploadResponse
from app.utils.s3 import build_s3_path

from tests.utils import (
    MISSING_ID,
    PROJECT_ID,
    TEST_DATA_DIR,
    VIRTUAL_LAB_ID,
    add_db,
    assert_request,
    create_cell_morphology_id,
    route,
    s3_key_exists,
    s3_multipart_upload_exists,
    upload_entity_asset,
)

DIFFERENT_ENTITY_TYPE = "experimental_bouton_density"

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
FILE_EXAMPLE_DIGEST = "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91"
FILE_EXAMPLE_SIZE = 31

EMPTY_FILE_PATH = TEST_DATA_DIR / "empty.txt"
EMPTY_FILE_DIGEST = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EMPTY_FILE_SIZE = 0

DUMMY_DIGEST = "a" * 64


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
def create_entity_asset(subject_id, brain_region_id, cell_morphology_protocol_id):
    def _create_entity_asset(
        client,
        authorized_public,
    ):
        entity_type = EntityType.cell_morphology
        entity_id = create_cell_morphology_id(
            client,
            subject_id=subject_id,
            brain_region_id=brain_region_id,
            cell_morphology_protocol_id=cell_morphology_protocol_id,
            authorized_public=authorized_public,
        )
        data = (
            _upload_entity_asset(
                client,
                entity_type=entity_type,
                entity_id=entity_id,
                label="morphology",
                file_upload_name="morph.asc",
                content_type="application/asc",
            )
            .raise_for_status()
            .json()
        )
        return entity_id, entity_type, data["id"]

    return _create_entity_asset


@pytest.fixture
def entity(client, subject_id, brain_region_id, cell_morphology_protocol_id) -> Entity:
    entity_type = EntityType.cell_morphology
    entity_id = create_cell_morphology_id(
        client,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=False,
    )
    return Entity(id=entity_id, type=entity_type)


def _upload_entity_asset(
    client,
    entity_type,
    entity_id,
    label,
    file_upload_name,
    content_type,
    expected_status=None,
    filepath=FILE_EXAMPLE_PATH,
):
    with filepath.open("rb") as f:
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
def uploading_asset(client, entity) -> AssetRead:
    """Create an asset the file of which is being uploaded with delegation."""
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json={
            "filename": "foo.swc",
            "filesize": 3 * 5 * 1024**2,
            "sha256_digest": DUMMY_DIGEST,
            "preferred_part_count": 3,
            "label": "morphology",
            "content_type": "application/swc",
        },
    ).json()
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


@pytest.fixture
def private_asset_directory(db, circuit, person_id) -> Asset:
    s3_path = _get_expected_full_path(entity=circuit, path="my-directory")
    asset = Asset(
        path="my-directory",
        full_path=s3_path,
        status="created",
        is_directory=True,
        content_type="application/vnd.directory",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=circuit.id,
        created_by_id=person_id,
        updated_by_id=person_id,
        label="sonata_circuit",
        storage_type=StorageType.aws_s3_internal,
    )
    add_db(db, asset)
    return asset


def test_upload_entity_asset(client, entity, monkeypatch):
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

    # try to upload a file w/ an invalid content type
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
    assert error.error_code == ApiErrorCode.ASSET_INVALID_SCHEMA
    assert "Value error, morphology implies one of the following content-types" in error.details[0]

    # upload an empty file
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="empty_morph.asc",
        content_type="application/asc",
        filepath=EMPTY_FILE_PATH,
    )
    assert response.status_code == 201, f"Failed to create asset: {response.text}"
    data = response.json()

    expected_full_path = _get_expected_full_path(entity, path="empty_morph.asc")
    assert data == {
        "id": ANY,
        "path": "empty_morph.asc",
        "full_path": expected_full_path,
        "is_directory": False,
        "content_type": "application/asc",
        "size": EMPTY_FILE_SIZE,
        "sha256_digest": EMPTY_FILE_DIGEST,
        "meta": {},
        "status": "created",
        "label": "morphology",
        "storage_type": StorageType.aws_s3_internal,
    }

    # try to upload a file too big
    with monkeypatch.context() as m:
        m.setattr(settings, "API_ASSET_POST_MAX_SIZE", 1)
        response = _upload_entity_asset(
            client,
            entity_type=entity.type,
            entity_id=entity.id,
            label="morphology",
            file_upload_name="big_morph.asc",
            content_type="application/asc",
        )
        assert response.status_code == 422, (
            f"Asset creation didn't fail as expected: {response.text}"
        )
        error = ErrorResponse.model_validate(response.json())
        assert error.error_code == ApiErrorCode.ASSET_INVALID_FILE


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
            (
                f"Value error, Asset label '{AssetLabel.morphology}' is not allowed for "
                f"entity type '{entity.type}'. "
                f"Allowed asset labels: ['{AssetLabel.cell_composition_summary}']"
            )
        ],
    }


def test_upload_entity_asset_invalid_content_type(client, entity):
    """Test upload with a file whose extension maps to an unsupported content type."""
    response = _upload_entity_asset(
        client,
        entity_type=entity.type,
        entity_id=entity.id,
        label="morphology",
        file_upload_name="data.xyz",
        content_type="chemical/x-xyz",
    )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_CONTENT_TYPE
    assert "Invalid content type" in error.message


def test_upload_entity_asset_s3_failure(client, entity):
    """Test upload when S3 upload fails."""
    with patch("app.service.asset.upload_to_s3", return_value=False):
        response = _upload_entity_asset(
            client,
            entity_type=entity.type,
            entity_id=entity.id,
            label="morphology",
            file_upload_name="morph.asc",
            content_type="application/asc",
        )
    assert response.status_code == 500
    assert response.json()["details"] == "Failed to upload object"


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
    ("full_path", "expected_error"),
    [
        ("/test.swc", "Absolute paths are forbidden"),
        ("", "Empty paths are forbidden"),
        ("path/to/../test.swc", "Parent traversal is forbidden"),
    ],
)
def test_register_entity_asset_with_invalid_full_path(client, entity, full_path, expected_error):
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
    assert response.json()["details"][0]["msg"] == f"Value error, {expected_error}"


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


def test_download_entity_asset(clients, entity, asset):

    response = assert_request(
        clients.user_1.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        expected_status_code=307,
        follow_redirects=False,
    )
    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
    expected_params = {"AWSAccessKeyId", "Signature", "Expires"}
    assert response.next_request.url.path.endswith(expected_full_path)
    assert expected_params.issubset(response.next_request.url.params)

    # user 2 has no access to entity
    assert_request(
        clients.user_2.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        expected_status_code=404,
        follow_redirects=False,
    )

    # cheeky user cannot use admin endpoint
    assert_request(
        clients.user_1.get,
        url=f"/admin{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        expected_status_code=403,
    )

    # admin cannot have access through regular endpoint
    assert_request(
        clients.admin.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        expected_status_code=404,
    )

    # admin can use admin endpoint
    response = assert_request(
        clients.admin.get,
        url=f"/admin{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        expected_status_code=307,
        follow_redirects=False,
    )
    expected_full_path = _get_expected_full_path(entity, path="morph.asc")
    expected_params = {"AWSAccessKeyId", "Signature", "Expires"}
    assert response.next_request.url.path.endswith(expected_full_path)
    assert expected_params.issubset(response.next_request.url.params)

    # try to download an asset with non-existent entity id
    data = assert_request(
        clients.user_1.get,
        url=f"{route(entity.type)}/{MISSING_ID}/assets/{asset.id}/download",
        expected_status_code=404,
    ).json()
    error = ErrorResponse.model_validate(data)
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND

    # try to download an asset with non-existent asset id
    data = assert_request(
        clients.user_1.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}/download",
        expected_status_code=404,
    ).json()
    error = ErrorResponse.model_validate(data)
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND

    # when downloading a single file asset_path should not be passed as a parameter
    assert_request(
        clients.user_1.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
        params={"asset_path": "foo"},
        follow_redirects=False,
        expected_status_code=409,
    )


def test_download_entity_asset__uploading(client, entity, uploading_asset):
    """Test that downloading an uploading asset is forbidden."""

    response = client.get(
        f"{route(entity.type)}/{entity.id}/assets/{uploading_asset.id}/download",
        follow_redirects=False,
    )
    assert response.status_code == HTTPStatus.CONFLICT
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_UPLOAD_INCOMPLETE


@pytest.mark.parametrize("client_fixture", ["client_user_2", "client_no_project"])
def test_download_entity_asset_non_authorized(request, client_fixture, entity, asset):
    client = request.getfixturevalue(client_fixture)

    response = client.get(f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download")
    assert response.status_code == 404, f"Unexpected result: {response.text}"
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


@pytest.mark.parametrize(
    ("is_public", "client_name", "expected_status_code", "expected_error"),
    [
        (False, "user_1", 200, None),  # project admin, same project
        (
            True,
            "user_1",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # project admin cannot delete public ones
        (
            False,
            "user_2",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # project admin, diff project, no creator
        (
            True,
            "user_2",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # project admin, diff project, no creator
        (
            False,
            "user_3",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # project member, same project, no creator
        (
            True,
            "user_3",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # project member, same project, no creator
        (False, "no_project", 403, ApiErrorCode.ENTITY_FORBIDDEN),  # no project ids
        (True, "no_project", 403, ApiErrorCode.ENTITY_FORBIDDEN),  # no project ids
        (False, "maintainer_1", 200, None),  # same project
        (True, "maintainer_1", 200, None),  # same project
        (False, "maintainer_2", 403, ApiErrorCode.ENTITY_FORBIDDEN),  # diff project,
        (True, "maintainer_2", 403, ApiErrorCode.ENTITY_FORBIDDEN),  # diff project,
        (
            False,
            "admin",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # regular route, admin is treated as a user
        (
            True,
            "admin",
            403,
            ApiErrorCode.ENTITY_FORBIDDEN,
        ),  # regular route, admin is treated as a user
    ],
)
def test_delete_entity_asset__authorization__user(
    clients, create_entity_asset, is_public, client_name, expected_status_code, expected_error
):
    entity_id, entity_type, asset_id = create_entity_asset(
        clients.user_1, authorized_public=is_public
    )

    data = assert_request(
        client_method=getattr(clients, client_name).delete,
        url=f"{route(entity_type)}/{entity_id}/assets/{asset_id}",
        expected_status_code=expected_status_code,
    ).json()

    if expected_error is not None:
        assert ErrorResponse.model_validate(data).error_code == expected_error


@pytest.mark.parametrize(
    ("is_public", "client_name", "expected_status_code", "expected_error"),
    [
        (True, "admin", 200, None),
        (False, "admin", 200, None),
        (True, "user_1", 403, ApiErrorCode.NOT_AUTHORIZED),
        (False, "user_2", 403, ApiErrorCode.NOT_AUTHORIZED),
        (True, "user_2", 403, ApiErrorCode.NOT_AUTHORIZED),
        (False, "user_3", 403, ApiErrorCode.NOT_AUTHORIZED),
        (True, "user_3", 403, ApiErrorCode.NOT_AUTHORIZED),
        (False, "no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
        (True, "no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
        (False, "maintainer_1", 403, ApiErrorCode.NOT_AUTHORIZED),
        (True, "maintainer_1", 403, ApiErrorCode.NOT_AUTHORIZED),
        (False, "maintainer_2", 403, ApiErrorCode.NOT_AUTHORIZED),
        (True, "maintainer_2", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_delete_entity_asset__authorization__admin(
    clients, create_entity_asset, is_public, client_name, expected_status_code, expected_error
):
    entity_id, entity_type, asset_id = create_entity_asset(
        clients.user_1, authorized_public=is_public
    )

    data = assert_request(
        client_method=getattr(clients, client_name).delete,
        url=f"admin{route(entity_type)}/{entity_id}/assets/{asset_id}",
        expected_status_code=expected_status_code,
    ).json()

    if expected_error is not None:
        assert ErrorResponse.model_validate(data).error_code == expected_error


@pytest.mark.parametrize(
    ("is_public", "expected_status_code", "expected_error"),
    [
        (False, 200, None),
        (True, 403, ApiErrorCode.ENTITY_FORBIDDEN),
    ],
)
def test_delete_entity_asset__authorization__user_own(
    clients, create_entity_asset, is_public, expected_status_code, expected_error
):
    """Test project member may delete their own private assets."""
    entity_id, entity_type, asset_id = create_entity_asset(
        clients.user_3, authorized_public=is_public
    )

    data = assert_request(
        client_method=clients.user_3.delete,
        url=f"{route(entity_type)}/{entity_id}/assets/{asset_id}",
        expected_status_code=expected_status_code,
    ).json()

    if expected_error is not None:
        assert ErrorResponse.model_validate(data).error_code == expected_error


def test_delete_entity_asset(client, entity, asset):
    response = client.delete(f"{route(entity.type)}/{entity.id}/assets/{asset.id}")
    assert response.status_code == 200, f"Failed to delete asset: {response.text}"

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


def test_asset_deletion_cascade(db, client, create_entity_asset, s3):
    """Test that the deletion of an entity triggers Asset and s3 file deletions."""

    entity_id, entity_type, asset_id = create_entity_asset(client, authorized_public=False)

    assert db.get(Entity, entity_id)
    db_asset = db.get(Asset, asset_id)
    assert s3_key_exists(s3, key=db_asset.full_path)

    assert_request(client.delete, url=f"{route(entity_type)}/{entity_id}")

    assert not db.get(Entity, entity_id)
    assert not db.get(Asset, asset_id)
    assert not s3_key_exists(s3, key=db_asset.full_path)


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

    # test that the deleted assets are not returned
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
        error = ErrorResponse.model_validate(response.json())
        assert error.details[0]["type"] == "too_short"

    duplicate_path = ["path/to/file", "path/to/file"]
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={"files": duplicate_path, "meta": None, "label": label, "directory_name": "test3"},
        )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert error.details[0]["msg"] == "Value error, Filenames must be unique within the directory."

    invalid_files = [
        "/absolute/path/file.txt",
        "../../../etc/passwd",
        "valid/path/../../../etc/groups",
        ".",
        "",
    ]
    with mock_aws():
        response = client.post(
            f"{entity_type}/{entity_id}/assets/directory/upload",
            json={"files": invalid_files, "meta": None, "label": label, "directory_name": "test4"},
        )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert [d["msg"] for d in error.details] == [
        "Value error, Absolute paths are forbidden",
        "Value error, Parent traversal is forbidden",
        "Value error, Parent traversal is forbidden",
        "Value error, Empty paths are forbidden",
        "Value error, Empty paths are forbidden",
    ]


def test_list_entity_asset_directory(
    clients, root_circuit, circuit, private_asset_directory, asset_directory
):
    entity_type = route(root_circuit.type)
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

    with patch("app.service.asset.list_directory_with_details") as mock_list_directory:
        mock_list_directory.return_value = fake_files

        data = assert_request(
            clients.user_1.get,
            url=f"{entity_type}/{circuit.id}/assets/{private_asset_directory.id}/list",
        ).json()

        assert "files" in data
        assert data["files"] == fake_files

    with patch("app.service.asset.list_directory_with_details") as mock_list_directory:
        mock_list_directory.return_value = fake_files

        # user 2 cannot acces the private directory of user 1
        data = assert_request(
            clients.user_2.get,
            url=f"{entity_type}/{circuit.id}/assets/{private_asset_directory.id}/list",
            expected_status_code=404,
        ).json()

        # only if public
        data = assert_request(
            clients.user_2.get,
            url=f"{entity_type}/{root_circuit.id}/assets/{asset_directory.id}/list",
        ).json()

        assert "files" in data
        assert data["files"] == fake_files

    with patch("app.service.asset.list_directory_with_details") as mock_list_directory:
        mock_list_directory.return_value = fake_files

        # when no project the user can access public directories
        data = assert_request(
            clients.no_project.get,
            url=f"{entity_type}/{root_circuit.id}/assets/{asset_directory.id}/list",
        ).json()

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
        ("client_no_project", 404, ApiErrorCode.ENTITY_NOT_FOUND),
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


def _multipart_json_data(
    filesize=3 * 5 * 1024**2, filename="foo.swc", content_type="application/swc"
):
    return {
        "filename": filename,
        "filesize": filesize,
        "sha256_digest": DUMMY_DIGEST,
        "preferred_part_count": 3,
        "label": "morphology",
        "content_type": content_type,
    }


def test_multipart_asset_upload(db, client, entity, s3, s3_internal_bucket):
    """Test iniating, uploading parts, and completing a multipart upload."""
    filesize = 3 * 5 * 1024**2

    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filesize),
    ).json()

    upload_id = db.get(Asset, data["id"]).upload_meta["upload_id"]

    expected_upload_meta = {
        "part_size": 5 * 1024**2,
        "parts": [
            {
                "part_number": 1,
                "url": ANY,
            },
            {
                "part_number": 2,
                "url": ANY,
            },
            {
                "part_number": 3,
                "url": ANY,
            },
        ],
    }

    assert data["status"] == "uploading"
    assert data["upload_meta"] == expected_upload_meta

    # check that asset is registered in the db with uploading status
    asset_data = assert_request(
        client.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
    ).json()
    assert asset_data["status"] == "uploading"

    # check that multipart upload has initiated
    assert s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)

    # three lines with repeating a, b, c of 5Mb each
    file_part_bytes = [(letter * 5_242_879 + "\n").encode("utf-8") for letter in ("a", "b", "c")]

    # upload the file to s3 using parts (no presigned urls)
    part_size = data["upload_meta"]["part_size"]
    n_full_parts, remainder = divmod(filesize, part_size)
    sizes = [part_size] * n_full_parts
    if remainder:
        sizes += [remainder]

    assert len(sizes) == len(data["upload_meta"]["parts"])

    for i, part in enumerate(data["upload_meta"]["parts"]):
        s3.upload_part(
            Bucket=s3_internal_bucket,
            Key=data["full_path"],
            UploadId=upload_id,
            PartNumber=part["part_number"],
            Body=file_part_bytes[i],
        )

    # sanity check that part data is uploaded
    parts = s3.list_parts(
        Bucket=s3_internal_bucket,
        Key=data["full_path"],
        UploadId=upload_id,
    )["Parts"]

    assert len(parts) == 3
    for i, part in enumerate(parts, start=1):
        assert part["PartNumber"] == i
        assert part["Size"] == part_size

    completed_data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}/multipart-upload/complete",
    ).json()

    assert completed_data["status"] == "created"

    # sanity check if db asset changes persisted
    completed_data = assert_request(
        client.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
    ).json()
    assert completed_data["status"] == "created"

    # get file from s3 and check concatenation is correct
    content = s3.get_object(Bucket=s3_internal_bucket, Key=data["full_path"])["Body"].read()
    assert content == b"".join(file_part_bytes)

    # check no uploads left following completion
    assert not s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)


def test_multipart_asset_upload_abort(db, client, entity, s3, s3_internal_bucket):
    filesize = 3 * 5 * 1024**2

    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filesize),
    ).json()

    assert data["status"] == "uploading"
    upload_id = db.get(Asset, data["id"]).upload_meta["upload_id"]

    # check that asset is registered in the db with uploading status
    asset_data = assert_request(
        client.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
    ).json()
    assert asset_data["status"] == "uploading"

    # check that multipart upload has initiated
    assert s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)

    assert_request(
        client.delete,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
    )

    # uploading asset must be deleted
    assert_request(
        client.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
        expected_status_code=404,
    )

    # check that the asset deletion triggered multipart upload abort
    assert not s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)


def test_entity_asset_multipart_upload_initiate__invalid_filesize(client, entity):
    """Test entity_asset_multipart_upload_initiate with invalid filesize."""
    # Test with filesize exceeding max
    max_size = settings.S3_MULTIPART_UPLOAD_MAX_SIZE
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filesize=max_size + 1),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert error.details[0]["msg"] == f"Input should be less than {max_size}"


def test_entity_asset_multipart_upload_initiate__invalid_filename(client, entity):
    """Test entity_asset_multipart_upload_initiate with invalid filename."""
    # Test with invalid filename (path traversal)

    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filename="../../etc/passwd"),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert error.message == "Validation error"
    assert error.details[0]["msg"] == "Value error, Expected a valid file or directory name"

    # Test with invalid filename (absolute path)
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filename="/absolute/path/file.swc"),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert error.message == "Validation error"
    assert error.details[0]["msg"] == "Value error, Expected a valid file or directory name"


def test_entity_asset_multipart_upload_initiate__invalid_content_type(client, entity):
    """Test entity_asset_multipart_upload_initiate with invalid content type."""
    # Test with invalid content type
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(content_type="application/octet-stream"),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_INVALID_SCHEMA
    assert "Value error, morphology implies one of the following content-types" in error.details[0]


def test_entity_asset_multipart_upload_initiate__duplicate(client, entity):
    """Test entity_asset_multipart_upload_initiate with duplicate asset."""
    # Create first upload
    assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(),
    )

    # Try to create duplicate
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(),
        expected_status_code=409,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED


def test_entity_asset_multipart_upload_initiate__entity_not_found(client, entity):
    """Test entity_asset_multipart_upload_initiate with non-existent entity."""
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{MISSING_ID}/assets/multipart-upload/initiate",
        json=_multipart_json_data(),
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_entity_asset_multipart_upload_initiate__non_authorized(
    request, client_fixture, expected_status, expected_error, entity
):
    """Test entity_asset_multipart_upload_initiate with unauthorized user."""
    client = request.getfixturevalue(client_fixture)
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(),
        expected_status_code=expected_status,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == expected_error


def test_entity_asset_multipart_upload_complete__asset_not_found(client, entity):
    """Test entity_asset_multipart_upload_complete with non-existent asset."""
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{MISSING_ID}/multipart-upload/complete",
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


def test_entity_asset_multipart_upload_complete__entity_not_found(client, entity, uploading_asset):
    """Test entity_asset_multipart_upload_complete with non-existent entity."""
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{MISSING_ID}/assets/{uploading_asset.id}/multipart-upload/complete",
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_entity_asset_multipart_upload_complete__not_uploading(client, entity, asset):
    """Test entity_asset_multipart_upload_complete when asset is not in uploading status."""
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{asset.id}/multipart-upload/complete",
        expected_status_code=422,
    ).json()
    error = ErrorResponse.model_validate(data)
    assert error.error_code == ApiErrorCode.ASSET_NOT_UPLOADING
    assert "not uploading" in error.message.lower()


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_entity_asset_multipart_upload_complete__non_authorized(
    request, client_fixture, expected_status, expected_error, entity, uploading_asset
):
    """Test entity_asset_multipart_upload_complete with unauthorized user."""
    client = request.getfixturevalue(client_fixture)
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{uploading_asset.id}/multipart-upload/complete",
        expected_status_code=expected_status,
    ).json()
    error = ErrorResponse.model_validate(data)
    assert error.error_code == expected_error


def test_entity_asset_multipart_upload_complete__incomplete(
    db, client, entity, s3, s3_internal_bucket
):
    """Test entity_asset_multipart_upload_complete when upload is incomplete."""
    filesize = 3 * 5 * 1024**2

    # Initiate upload
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filesize=filesize),
    ).json()

    upload_id = db.get(Asset, data["id"]).upload_meta["upload_id"]

    # Upload only 2 out of 3 parts (incomplete)
    file_part_bytes = [(letter * 5_242_879 + "\n").encode("utf-8") for letter in ("a", "b")]

    for i, part in enumerate(data["upload_meta"]["parts"][:2]):  # Only upload 2 parts
        s3.upload_part(
            Bucket=s3_internal_bucket,
            Key=data["full_path"],
            UploadId=upload_id,
            PartNumber=part["part_number"],
            Body=file_part_bytes[i],
        )

    # Try to complete - should fail because not all parts are uploaded
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}/multipart-upload/complete",
        expected_status_code=409,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_UPLOAD_INCOMPLETE
    assert "Expected parts are not uploaded" in error.message

    # upload last part
    s3.upload_part(
        Bucket=s3_internal_bucket,
        Key=data["full_path"],
        UploadId=upload_id,
        PartNumber=data["upload_meta"]["parts"][-1]["part_number"],
        Body=file_part_bytes[-1],
    )

    # now should complete
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}/multipart-upload/complete",
    ).json()

    assert data["status"] == "created"


def test_entity_asset_multipart_upload_complete__inconsistent_size(
    db, client, entity, s3, s3_internal_bucket
):
    """Test entity_asset_multipart_upload_complete when uploaded size doesn't match expected."""
    # Expected filesize declared during initiation
    declared_filesize = 3 * 5 * 1024**2  # ~75MB

    # Initiate upload
    data = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/multipart-upload/initiate",
        json=_multipart_json_data(filesize=declared_filesize),
    ).json()

    upload_meta = data["upload_meta"]
    upload_id = db.get(Asset, data["id"]).upload_meta["upload_id"]

    # Upload *all* parts, but with incorrect sizes
    # Make each part slightly smaller so total size mismatches
    wrong_part_size = 5_242_000  # slightly smaller than expected
    body = b"x" * wrong_part_size

    for part in upload_meta["parts"]:
        s3.upload_part(
            Bucket=s3_internal_bucket,
            Key=data["full_path"],
            UploadId=upload_id,
            PartNumber=part["part_number"],
            Body=body,
        )

    # Try to complete - should fail due to size mismatch
    response = assert_request(
        client.post,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}/multipart-upload/complete",
        expected_status_code=409,
    )

    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE
    assert "does not match expected size" in error.message

    # Asset should still be in uploading state
    asset_data = assert_request(
        client.get,
        url=f"{route(entity.type)}/{entity.id}/assets/{data['id']}",
    ).json()
    assert asset_data["status"] == "uploading"


def test_download_entity_asset_presigned_url_generation_failure(client, entity, asset):
    with patch("app.service.asset.generate_presigned_url", return_value=None):
        response = client.get(
            f"{route(entity.type)}/{entity.id}/assets/{asset.id}/download",
            follow_redirects=False,
        )
    assert response.status_code == 500
    assert response.json() == {
        "details": "Failed to generate presigned url",
        "error_code": "GENERIC_ERROR",
        "message": "HTTP error",
    }


def test_upload_entity_asset_directory_presigned_url_generation_failure(client, root_circuit):
    with patch("app.service.asset.generate_presigned_url", return_value=None):
        response = client.post(
            f"{route(root_circuit.type)}/{root_circuit.id}/assets/directory/upload",
            json={
                "files": ["morphology/cell1.swc"],
                "meta": None,
                "label": "sonata_circuit",
                "directory_name": "test-presign-failure",
            },
        )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL


def _multipart_directory_json_data(
    directory_name="my-dir",
    label="sonata_circuit",
    files=None,
):
    if files is None:
        files = [
            {
                "filename": "morphology/cell1.swc",
                "filesize": 3 * 5 * 1024**2,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
            {
                "filename": "morphology/cell2.swc",
                "filesize": 3 * 5 * 1024**2,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
        ]
    return {
        "directory_name": directory_name,
        "label": label,
        "meta": {"key": "value"},
        "files": files,
    }


def _extract_upload_id(url):
    """Extract and return uploadId from a presigned url, only for tests."""
    return parse_qs(urlparse(url).query)["uploadId"][0]


def test_multipart_directory_upload(client, root_circuit, s3, s3_internal_bucket):
    """Test initiating, uploading parts, and completing a multipart directory upload."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id
    filesize = 3 * 5 * 1024**2

    json_data = _multipart_directory_json_data(
        files=[
            {
                "filename": "data/file1.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
            {
                "filename": "data/file2.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
        ]
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    assert "asset" in data
    assert "files" in data

    parent_asset = data["asset"]
    assert parent_asset["is_directory"] is True
    assert parent_asset["status"] == "uploading"
    assert parent_asset["label"] == "sonata_circuit"
    assert parent_asset["meta"] == {"key": "value"}

    file_assets = data["files"]
    assert len(file_assets) == 2

    for file_asset in file_assets:
        assert file_asset["status"] == "uploading"
        assert file_asset["upload_meta"] is not None
        assert len(file_asset["upload_meta"]["parts"]) == 3

    initiated = MultipartDirectoryUploadResponse.model_validate(data)

    # Upload parts for each file
    for file_asset in initiated.files:
        assert file_asset.upload_meta
        part_size = file_asset.upload_meta.part_size
        for part in file_asset.upload_meta.parts:
            upload_id = _extract_upload_id(part.url)
            s3.upload_part(
                Bucket=s3_internal_bucket,
                Key=file_asset.full_path,
                UploadId=upload_id,
                PartNumber=part.part_number,
                Body=b"x" * part_size,
            )

    # Complete the directory upload
    completed = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{parent_asset['id']}/directory/multipart-upload/complete",
    ).json()

    assert completed["status"] == "created"
    assert completed["is_directory"] is True

    # Verify parent asset is listed (children are not)
    assets_response = assert_request(
        client.get,
        url=f"{entity_type}/{entity_id}/assets",
    ).json()
    asset_ids = [a["id"] for a in assets_response["data"]]
    assert parent_asset["id"] in asset_ids
    for file_asset in file_assets:
        assert file_asset["id"] not in asset_ids


def test_multipart_directory_upload_entity_not_found(client, root_circuit):
    """Test initiate multipart directory upload with non-existent entity."""
    response = assert_request(
        client.post,
        url=f"{route(root_circuit.type)}/{MISSING_ID}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(),
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_multipart_directory_upload_duplicate(client, root_circuit):
    """Test initiate multipart directory upload with duplicate directory name."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(directory_name="dup-dir"),
    )

    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(directory_name="dup-dir"),
        expected_status_code=409,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_DUPLICATED


def test_multipart_directory_upload_invalid_directory_name(client, root_circuit):
    """Test initiate multipart directory upload with invalid directory names."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    # nested directory name
    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(directory_name="nested/dir"),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST


def test_multipart_directory_upload_empty_files(client, root_circuit):
    """Test initiate multipart directory upload with empty files list."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(files=[]),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.details[0]["type"] == "too_short"


def test_multipart_directory_upload_duplicate_filenames(client, root_circuit):
    """Test initiate multipart directory upload with duplicate filenames."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    dup_files = [
        {"filename": "same/file.bin", "filesize": 5 * 1024**2, "sha256_digest": DUMMY_DIGEST},
        {"filename": "same/file.bin", "filesize": 5 * 1024**2, "sha256_digest": DUMMY_DIGEST},
    ]
    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(files=dup_files),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert "Filenames must be unique" in error.details[0]["msg"]


def test_multipart_directory_upload_invalid_file_paths(client, root_circuit):
    """Test initiate multipart directory upload with invalid file paths."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    invalid_files = [
        {"filename": "/absolute/path.bin", "filesize": 5 * 1024**2, "sha256_digest": DUMMY_DIGEST},
    ]
    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(files=invalid_files),
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST
    assert "Absolute paths are forbidden" in error.details[0]["msg"]


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, ApiErrorCode.ENTITY_NOT_FOUND),
        ("client_no_project", 403, ApiErrorCode.NOT_AUTHORIZED),
    ],
)
def test_multipart_directory_upload_non_authorized(
    request, client_fixture, expected_status, expected_error, root_circuit
):
    """Test initiate multipart directory upload with unauthorized user."""
    client = request.getfixturevalue(client_fixture)
    response = assert_request(
        client.post,
        url=f"{route(root_circuit.type)}/{root_circuit.id}/assets/directory/multipart-upload/initiate",
        json=_multipart_directory_json_data(),
        expected_status_code=expected_status,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == expected_error


def test_complete_multipart_directory_upload_not_uploading(client, root_circuit, asset_directory):
    """Test complete multipart directory upload when asset is not in uploading status."""
    response = assert_request(
        client.post,
        url=f"{route(root_circuit.type)}/{root_circuit.id}/assets/{asset_directory.id}/directory/multipart-upload/complete",
        expected_status_code=422,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_UPLOADING


def test_complete_multipart_directory_upload_asset_not_found(client, root_circuit):
    """Test complete multipart directory upload with non-existent asset."""
    response = assert_request(
        client.post,
        url=f"{route(root_circuit.type)}/{root_circuit.id}/assets/{MISSING_ID}/directory/multipart-upload/complete",
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_NOT_FOUND


def test_complete_multipart_directory_upload_entity_not_found(client, root_circuit):
    """Test complete multipart directory upload with non-existent entity."""
    response = assert_request(
        client.post,
        url=f"{route(root_circuit.type)}/{MISSING_ID}/assets/{MISSING_ID}/directory/multipart-upload/complete",
        expected_status_code=404,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_complete_multipart_directory_upload_partial_already_completed(
    db, client, root_circuit, s3, s3_internal_bucket
):
    """Test completing a directory upload when one child is already completed."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id
    filesize = 3 * 5 * 1024**2

    json_data = _multipart_directory_json_data(
        directory_name="partial-dir",
        files=[
            {
                "filename": "file1.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
            {
                "filename": "file2.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_id = data["asset"]["id"]
    file_assets = data["files"]

    # Upload parts for both files
    part_size = file_assets[0]["upload_meta"]["part_size"]
    for file_asset in file_assets:
        upload_id = db.get(Asset, file_asset["id"]).upload_meta["upload_id"]
        for part in file_asset["upload_meta"]["parts"]:
            s3.upload_part(
                Bucket=s3_internal_bucket,
                Key=file_asset["full_path"],
                UploadId=upload_id,
                PartNumber=part["part_number"],
                Body=b"x" * part_size,
            )

    # Manually complete the first child via the single-file complete endpoint
    assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{file_assets[0]['id']}/multipart-upload/complete",
    )

    # Now complete the directory — first child should be skipped
    completed = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{parent_id}/directory/multipart-upload/complete",
    ).json()

    assert completed["status"] == "created"


def test_multipart_directory_upload_with_empty_files(client, root_circuit, s3, s3_internal_bucket):
    """Test directory upload with a mix of regular and empty (zero-size) files."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id
    filesize = 3 * 5 * 1024**2

    json_data = _multipart_directory_json_data(
        directory_name="dir-with-empty",
        files=[
            {
                "filename": "data/regular.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
            {
                "filename": "data/empty.bin",
                "filesize": 0,
                "sha256_digest": DUMMY_DIGEST,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_asset = data["asset"]
    file_assets = data["files"]
    assert len(file_assets) == 2

    # Regular file should have multipart upload metadata
    regular_asset = file_assets[0]
    assert regular_asset["upload_meta"]["part_size"] == 5 * 1024**2
    assert len(regular_asset["upload_meta"]["parts"]) == 3

    # Empty file should have put_object presigned URL with part_size=0 and part_number=0
    empty_asset = file_assets[1]
    assert empty_asset["upload_meta"]["part_size"] == 0
    assert len(empty_asset["upload_meta"]["parts"]) == 1
    assert empty_asset["upload_meta"]["parts"][0]["part_number"] == 0

    initiated = MultipartDirectoryUploadResponse.model_validate(data)

    # Upload parts for the regular file
    regular = initiated.files[0]
    assert regular.upload_meta
    part_size = regular.upload_meta.part_size
    for part in regular.upload_meta.parts:
        upload_id = _extract_upload_id(part.url)
        s3.upload_part(
            Bucket=s3_internal_bucket,
            Key=regular.full_path,
            UploadId=upload_id,
            PartNumber=part.part_number,
            Body=b"x" * part_size,
        )

    # Upload the empty file using put_object
    empty = initiated.files[1]
    s3.put_object(Bucket=s3_internal_bucket, Key=empty.full_path, Body=b"")

    # Complete the directory upload
    completed = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{parent_asset['id']}/directory/multipart-upload/complete",
    ).json()

    assert completed["status"] == "created"
    assert completed["is_directory"] is True

    # Verify the empty file exists in S3 with size 0
    head = s3.head_object(Bucket=s3_internal_bucket, Key=empty.full_path)
    assert head["ContentLength"] == 0


def test_multipart_directory_upload_empty_file_presigned_url_failure(client, root_circuit):
    """Test that initiate fails when presigned URL generation fails for empty file."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    json_data = _multipart_directory_json_data(
        directory_name="dir-empty-presign-fail",
        files=[
            {
                "filename": "data/empty.bin",
                "filesize": 0,
                "sha256_digest": DUMMY_DIGEST,
            },
        ],
    )

    with patch("app.service.asset.generate_presigned_url", return_value=None):
        response = assert_request(
            client.post,
            url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
            json=json_data,
            expected_status_code=422,
        )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL


def test_multipart_directory_upload_empty_file_check_object_error(client, root_circuit):
    """Test that complete fails when check_object raises an exception for empty file."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    json_data = _multipart_directory_json_data(
        directory_name="dir-empty-check-err",
        files=[
            {
                "filename": "data/empty.bin",
                "filesize": 0,
                "sha256_digest": DUMMY_DIGEST,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_id = data["asset"]["id"]

    with patch("app.service.asset.check_object", side_effect=RuntimeError("S3 error")):
        response = assert_request(
            client.post,
            url=f"{entity_type}/{entity_id}/assets/{parent_id}/directory/multipart-upload/complete",
            expected_status_code=500,
        )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.GENERIC_ERROR


def test_multipart_directory_upload_empty_file_not_uploaded(client, root_circuit):
    """Test completing directory upload fails when empty file was not uploaded to S3."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    json_data = _multipart_directory_json_data(
        directory_name="dir-empty-missing",
        files=[
            {
                "filename": "data/empty.bin",
                "filesize": 0,
                "sha256_digest": DUMMY_DIGEST,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_id = data["asset"]["id"]

    # Do NOT upload the empty file — complete should fail
    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{parent_id}/directory/multipart-upload/complete",
        expected_status_code=409,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_UPLOAD_INCOMPLETE


def test_multipart_directory_upload_empty_file_wrong_size(
    client, root_circuit, s3, s3_internal_bucket
):
    """Test completing directory upload fails when file declared as empty has non-zero size."""
    entity_type = route(root_circuit.type)
    entity_id = root_circuit.id

    json_data = _multipart_directory_json_data(
        directory_name="dir-empty-wrong-size",
        files=[
            {
                "filename": "data/empty.bin",
                "filesize": 0,
                "sha256_digest": DUMMY_DIGEST,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_id = data["asset"]["id"]
    empty_asset = data["files"][0]

    # Upload a non-empty file instead
    s3.put_object(Bucket=s3_internal_bucket, Key=empty_asset["full_path"], Body=b"not empty")

    # Complete should fail due to size mismatch
    response = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/{parent_id}/directory/multipart-upload/complete",
        expected_status_code=409,
    )
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE


def test_multipart_directory_upload_abort(db, client, circuit, s3, s3_internal_bucket):
    """Test that deleting a directory asset aborts multipart uploads for children."""
    entity_type = route(circuit.type)
    entity_id = circuit.id
    filesize = 3 * 5 * 1024**2

    json_data = _multipart_directory_json_data(
        directory_name="abort-dir",
        files=[
            {
                "filename": "file.bin",
                "filesize": filesize,
                "sha256_digest": DUMMY_DIGEST,
                "preferred_part_count": 3,
            },
        ],
    )

    data = assert_request(
        client.post,
        url=f"{entity_type}/{entity_id}/assets/directory/multipart-upload/initiate",
        json=json_data,
    ).json()

    parent_id = data["asset"]["id"]
    child_asset = data["files"][0]
    upload_id = db.get(Asset, child_asset["id"]).upload_meta["upload_id"]

    # Verify multipart upload exists
    assert s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)

    # Delete the parent directory asset
    assert_request(
        client.delete,
        url=f"{entity_type}/{entity_id}/assets/{parent_id}",
    )

    # Verify parent and child are deleted
    assert_request(
        client.get,
        url=f"{entity_type}/{entity_id}/assets/{parent_id}",
        expected_status_code=404,
    )

    # Verify multipart upload was aborted
    assert not s3_multipart_upload_exists(s3, upload_id, s3_internal_bucket)
