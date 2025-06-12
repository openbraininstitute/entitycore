"""Generic asset routes."""

import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.types import AssetLabel
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.db import RepoGroupDep
from app.dependencies.s3 import S3ClientDep
from app.errors import ApiError, ApiErrorCode
from app.schemas.asset import AssetAndPresignedURLS, AssetRead, FileList, DetailedFileList
from app.schemas.types import ListResponse, PaginationResponse
from app.service import asset as asset_service
from app.utils.files import calculate_sha256_digest, get_content_type
from app.utils.routers import EntityRoute, entity_route_to_type
from app.utils.s3 import (
    delete_from_s3,
    generate_presigned_url,
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
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    assets = asset_service.get_entity_assets(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
    )
    # TODO: proper pagination
    pagination = PaginationResponse(page=1, page_size=len(assets), total_items=len(assets))
    return ListResponse[AssetRead](data=assets, pagination=pagination)


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
    s3_client: S3ClientDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    file: UploadFile,
    meta: Annotated[dict | None, Form()] = None,
    label: Annotated[AssetLabel | None, Form()] = None,
) -> AssetRead:
    """Upload an asset to be associated with the specified entity.

    To be used only for small files. Use delegation for big files.
    """
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
    content_type = get_content_type(file)
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
    )
    if not upload_to_s3(
        s3_client,
        file_obj=file.file,
        bucket_name=settings.S3_BUCKET_NAME,
        s3_key=asset_read.full_path,
    ):
        raise HTTPException(status_code=500, detail="Failed to upload object")
    return asset_read


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep,
    user_context: UserContextDep,
    s3_client: S3ClientDep,
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
        if not validate_filename(asset_path):
            msg = f"Invalid file name {asset_path!r}"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_INVALID_PATH,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        full_path = str(Path(asset.full_path, asset_path))
    else:
        if asset_path:
            msg = "asset_path is only applicable when asset is a directory"
            raise ApiError(
                message=msg,
                error_code=ApiErrorCode.ASSET_NOT_A_DIRECTORY,
                http_status_code=HTTPStatus.CONFLICT,
            )
        full_path = asset.full_path

    url = generate_presigned_url(
        s3_client=s3_client,
        operation="get_object",
        bucket_name=settings.S3_BUCKET_NAME,
        s3_key=full_path,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


@router.delete("/{entity_route}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    s3_client: S3ClientDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The asset record is not deleted from the database, but its status is changed.
    The file is actually deleted from S3, unless using a versioning-enabled bucket.
    """
    asset = asset_service.delete_entity_asset(
        repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    if not delete_from_s3(s3_client, bucket_name=settings.S3_BUCKET_NAME, s3_key=asset.full_path):
        raise HTTPException(status_code=500, detail="Failed to delete object")
    return AssetRead.model_validate(asset)


@router.post("/{entity_route}/{entity_id}/assets/directory/upload")
def entity_asset_directory_upload(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    s3_client: S3ClientDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    files: FileList,
    # meta: Annotated[dict | None, Form()] = None,
    # label: Annotated[AssetLabel | None, Form()] = None,
) -> AssetAndPresignedURLS:
    """Given a list of full paths, return a dictionary of presigned URLS for uploading."""
    model, urls = asset_service.entity_asset_upload_directory(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        s3_client=s3_client,
        meta={},  # XXX
        label="swc",  # XXX
        files=files,
    )
    return AssetAndPresignedURLS.model_validate({"asset": model.dict(), "files": urls})


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}/list")
def entity_asset_directory_list(
    repos: RepoGroupDep,
    user_context: UserContextWithProjectIdDep,
    s3_client: S3ClientDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> DetailedFileList:
    """."""
    files = asset_service.list_directory(
        repos=repos,
        user_context=user_context,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        s3_client=s3_client,
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
