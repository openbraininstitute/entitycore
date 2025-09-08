"""Generic asset routes."""

import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import settings, storages
from app.db.types import AssetLabel, ContentType, StorageType
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import RepoGroupDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.errors import ApiError, ApiErrorCode
from app.filters.asset import AssetFilterDep
from app.schemas.asset import (
    AssetAndPresignedURLS,
    AssetRead,
    AssetRegister,
    DetailedFileList,
    DirectoryUpload,
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

    To be used only for small files. Use delegation for big files.
    """
    storage = storages[StorageType.aws_s3_internal]  # hardcoded for now
    s3_client = storage_client_factory(storage)
    if not file.size or not validate_filesize(file.size):
        msg = f"File bigger than {settings.API_ASSET_POST_MAX_SIZE}, please use delegation"
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
        size=file.size,
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
    asset = asset_service.get_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
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
    user_context: UserContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The asset record is not deleted from the database, but its status is changed.
    The file is actually deleted from S3, unless it's stored in open data storage.
    """
    asset = asset_service.delete_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    asset_service.delete_asset_storage_object(asset, storage_client_factory)
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


@router.post("/{entity_route}/{entity_id}/assets/upload/initiate", include_in_schema=False)
def initiate_entity_asset_upload(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    entity_route: EntityRoute,
    entity_id: int,
):
    """Generate a signed URL with expiration that can be used to upload the file directly to S3."""
    raise NotImplementedError


@router.post("/{entity_route}/{entity_id}/assets/upload/complete", include_in_schema=False)
def complete_entity_asset_upload(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    entity_route: EntityRoute,
    entity_id: int,
):
    """Register the uploaded file."""
    raise NotImplementedError
