"""Generic asset routes."""

import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import settings, storages
from app.db.types import AssetLabel, AssetStatus, ContentType, StorageType
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import RepoGroupDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.errors import ApiError, ApiErrorCode
from app.filters.asset import AssetFilterDep
from app.schemas.asset import (
    AssetAndPresignedURLS,
    AssetRead,
    AssetReadWithUploadMeta,
    AssetRegister,
    DetailedFileList,
    DirectoryUpload,
    InitiateUploadRequest,
)
from app.schemas.types import ListResponse
from app.service import asset as asset_service
from app.utils.files import calculate_sha256_digest, get_content_type
from app.utils.routers import EntityRoute, entity_route_to_type
from app.utils.s3 import (
    check_object,
    generate_presigned_url,
    sanitize_directory_traversal,
    upload_to_s3,
    validate_filename,
    validate_filesize,
    validate_multipart_filesize,
)

router = APIRouter(
    prefix="",
    tags=["assets"],
)


@router.get("/{entity_route}/{entity_id}/assets")
def get_entity_assets(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: AssetFilterDep,
) -> ListResponse[AssetRead]:
    """Retrieve a paginated list of assets associated with a specific entity.

    This endpoint returns all assets linked to the given `entity_route` and `entity_id`,
    subject to pagination and optional filtering parameters.

    Notes:
    - Assets with status `CREATED` are fully processed and available for download.
    - Assets with status `UPLOADING` may also be returned in the response. However,
      these assets are still being uploaded and are not yet complete. As a result,
      they cannot be downloaded until their status transitions to `CREATED`.
    - The presence of an asset in the response does not guarantee it is downloadable.
    - Clients should always check the asset `status` field before attempting to download.
    """
    return asset_service.get_entity_assets(
        repos=repos,
        user_context=user_context,
        entity_route=entity_route,
        entity_id=entity_id,
        pagination_request=pagination_request,
        filter_model=filter_model,
    )


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}")
def get_entity_asset(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Return the metadata of an assets associated with a specific entity."""
    return asset_service.get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )


@router.post("/{entity_route}/{entity_id}/assets", status_code=status.HTTP_201_CREATED)
def upload_entity_asset(
    *,
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    file: UploadFile,
    label: Annotated[AssetLabel, Form()],
    meta: Annotated[dict | None, Form()] = None,
) -> AssetRead:
    """Upload an asset to be associated with the specified entity.

    To be used only for small files.
    """
    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now
    s3_client = storage_client_factory(storage)
    if file.size and not validate_filesize(file.size):
        msg = f"File not allowed because empty or bigger than {settings.API_ASSET_POST_MAX_SIZE}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_FILE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    if not file.filename or not validate_filename(file.filename):
        msg = f"Invalid file name {file.filename!r}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    try:
        content_type = get_content_type(file)
    except ValueError as e:
        msg = (
            f"Invalid content type for file {file.filename}. "
            f"Supported content types: {sorted(c.value for c in ContentType)}.\n"
            f"Exception: {e}"
        )
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_CONTENT_TYPE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        ) from None

    sha256_digest = calculate_sha256_digest(file)
    asset_read = asset_service.create_entity_asset(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        filename=file.filename,
        content_type=content_type,
        size=file.size or 0,
        sha256_digest=sha256_digest,
        meta=meta,
        label=label,
        is_directory=False,
        storage_type=storage.type,
    )
    if not upload_to_s3(
        s3_client,
        file_obj=file.file,
        bucket_name=storage.bucket,
        s3_key=asset_read.full_path,
    ):
        raise HTTPException(status_code=500, detail="Failed to upload object")
    return asset_read


@router.post("/{entity_route}/{entity_id}/assets/register", status_code=status.HTTP_201_CREATED)
def register_entity_asset(
    *,
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset: AssetRegister,
) -> AssetRead:
    """Register an asset already in cloud.

    Only open data storage is supported for now.
    """
    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)

    try:
        check_result = check_object(
            s3_client,
            bucket_name=storage.bucket,
            s3_key=asset.full_path,
            is_directory=asset.is_directory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check object") from e

    if check_result["exists"] is False:
        raise ApiError(
            message="Object does not exist in S3",
            error_code=ApiErrorCode.ASSET_NOT_FOUND,
            http_status_code=HTTPStatus.CONFLICT,
            details={
                "bucket": storage.bucket,
                "region": storage.region,
                "s3_key": asset.full_path,
            },
        )

    asset_read = asset_service.create_entity_asset(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        filename=asset.path,
        content_type=asset.content_type,
        size=-1,  # considered unknown for already existing assets
        sha256_digest=None,  # considered unknown for already existing assets
        meta=asset.meta,
        label=asset.label,
        is_directory=asset.is_directory,
        storage_type=storage.type,
        full_path=asset.full_path,
    )
    return asset_read


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
    asset_path: str | None = None,
) -> RedirectResponse:
    """Download an asset associated with a specific entity.

    This endpoint returns a temporary download link (via HTTP redirect) to the
    requested asset file.

    Availability:
    - Only assets with status `CREATED` can be downloaded.
    - If the asset is in `UPLOADING` status, the request will return
      HTTP 409 (Conflict) because the asset is not yet complete.

    Directory assets:
    - If the asset represents a directory, you must provide the `asset_path`
      query parameter specifying the relative path of the file inside the directory.
    - If `asset_path` is missing for a directory asset, the request will fail
      with HTTP 409.
    - If `asset_path` is provided for a non-directory asset, the request will
      fail with HTTP 409.
    """
    asset = asset_service.get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    if asset.status == AssetStatus.UPLOADING:
        raise ApiError(
            message="Cannot download an uploading asset, because it is incomplete.",
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    if asset.is_directory:
        if asset_path is None:
            msg = "Missing required parameter for downloading a directory file: asset_path"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_MISSING_PATH,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = str(Path(asset.full_path, sanitize_directory_traversal(asset_path)))
    else:
        if asset_path:
            msg = "asset_path is only applicable when asset is a directory"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = asset.full_path

    storage = storages[asset.storage_type]
    s3_client = storage_client_factory(storage)

    url = generate_presigned_url(
        s3_client=s3_client,
        operation="get_object",
        bucket_name=storage.bucket,
        s3_key=full_path,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


@router.delete("/{entity_route}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The file is actually deleted from S3, unless it's stored in open data storage.
    """
    asset = asset_service.delete_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )

    # Note: Asset storage object is deleted via app.db.events

    return asset


@router.post("/{entity_route}/{entity_id}/assets/directory/upload")
def entity_asset_directory_upload(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    files: DirectoryUpload,
) -> AssetAndPresignedURLS:
    """Given a list of full paths, return a dictionary of presigned URLS for uploading."""
    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now
    s3_client = storage_client_factory(storage)
    if not files.directory_name or not validate_filename(str(files.directory_name)):
        msg = f"Invalid directory_name {files.directory_name!r}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    model, urls = asset_service.entity_asset_upload_directory(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        s3_client=s3_client,
        storage=storage,
        files=files,
    )
    return AssetAndPresignedURLS.model_validate({"asset": model.model_dump(), "files": urls})


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}/list")
def entity_asset_directory_list(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> DetailedFileList:
    """Return the list of files in a directory asset."""
    files = asset_service.list_directory(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        storage_client_factory=storage_client_factory,
        asset_id=asset_id,
    )
    return files


@router.post("/{entity_route}/{entity_id}/assets/multipart-upload/initiate")
def initiate_entity_asset_upload(
    repos: RepoGroupDep,
    storage_client_factory: StorageClientFactoryDep,
    user_context: UserContextWithProjectIdDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    json_model: InitiateUploadRequest,
) -> AssetReadWithUploadMeta:
    """Start a multipart upload for a file asset associated with an entity.

    This endpoint prepares the system and generates presigned URLs that you can
    use to upload a large file directly to S3 in multiple parts.

    **How it works:**
    1. The system checks that the file size does not exceed the allowed limit.
    2. The filename is validated to ensure it is safe to store.
    3. The file content type is checked to ensure it is supported.
    4. An asset record is created in the system with status `UPLOADING`.
    5. Presigned URLs are generated and returned. Use these URLs to upload
       the file parts directly to S3.

    After uploading all parts, you will need to call the completion endpoint
    to finalize the asset.

    **User notes:**
    - While in `UPLOADING` status, the asset is visible in the system but not yet complete.
    - If you lose the presigned URLs and wish to cancel the upload, you must
      delete the asset manually using the delete asset endpoint.
    """
    if not validate_multipart_filesize(json_model.filesize):
        msg = f"File not allowed because bigger than {settings.S3_MULTIPART_UPLOAD_MAX_SIZE}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_FILE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    if not validate_filename(json_model.filename):
        msg = f"Invalid file name {json_model.filename!r}"
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_PATH,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    try:
        content_type = get_content_type(json_model)
    except ValueError as e:
        msg = (
            f"Invalid content type for file {json_model.filename}. "
            f"Supported content types: {sorted(c.value for c in ContentType)}.\n"
            f"Exception: {e}"
        )
        raise ApiError(
            message=msg,
            error_code=ApiErrorCode.ASSET_INVALID_CONTENT_TYPE,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        ) from None

    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now
    s3_client = storage_client_factory(storage)

    entity_type = entity_route_to_type(entity_route)

    # create asset to fail early if full path already in progress or registered
    asset_read = asset_service.create_entity_asset(
        repos=repos,
        user_context=user_context,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=json_model.filename,
        content_type=content_type,
        size=json_model.filesize,
        sha256_digest=json_model.sha256_digest,
        meta=None,
        label=json_model.label,
        is_directory=False,
        storage_type=storage.type,
        status=AssetStatus.UPLOADING,
    )

    # create presigned urls using the part count hint and filesize
    # asset schemas is updated with the upload metadata
    # Note: User already authorized when creating the asset
    asset_read = asset_service.entity_asset_upload_initiate(
        repos=repos,
        s3_client=s3_client,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_read.id,
        bucket=storage.bucket,
        s3_key=asset_read.full_path,
        filesize=json_model.filesize,
        content_type=content_type,
        preferred_part_count=json_model.preferred_part_count,
    )

    return asset_read


@router.post("/{entity_route}/{entity_id}/assets/{asset_id}/multipart-upload/complete")
def complete_entity_asset_upload(
    repos: RepoGroupDep,
    storage_client_factory: StorageClientFactoryDep,
    user_context: UserContextWithProjectIdDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Finalize a multipart upload for a asset file associated with an entity.

    After uploading all file parts using the presigned URLs from the initiation
    endpoint, call this endpoint to complete the upload and make the file
    available in the system.

    **How it works:**
    1. The system verifies that the asset is currently in an `UPLOADING` state.
       If it is not, the operation is rejected.
    2. All uploaded parts in S3 are checked against the expected number of parts.
       If some parts are missing, the operation fails.
    3. The combined size of uploaded parts is verified against the expected
       file size. If there is a mismatch, the operation fails.
    4. Once all parts are verified, the system assembles them into the final file.
    5. The asset status is updated to `CREATED`, indicating that the file is
       officially available for use.

    **User notes:**
    - While in `UPLOADING` status, the asset is visible in the system but not yet complete.
    - If you lose the presigned URLs and wish to cancel the upload, you must
      delete the asset manually using the delete asset endpoint.
    """
    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now

    return asset_service.entity_asset_upload_complete(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
        storage=storage,
        s3_client=storage_client_factory(storage),
    )
