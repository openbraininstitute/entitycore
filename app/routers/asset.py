"""Generic asset routes."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.types import EntityWithAssets
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import RepoGroupDep
from app.dependencies.s3 import S3ClientDep
from app.errors import ApiError, ApiErrorCode
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.asset import AssetRead
from app.service import asset as asset_service
from app.utils.files import get_content_type
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


@router.get("/{entity_type}/{entity_id}/assets")
def get_entity_assets(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    entity_type: EntityWithAssets,
    entity_id: int,
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    assets = asset_service.get_entity_assets(
        repos,
        project_context=project_context,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    # TODO: proper pagination
    pagination = PaginationResponse(page=1, page_size=len(assets), total_items=len(assets))
    return ListResponse[AssetRead](data=assets, pagination=pagination)


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}")
def get_entity_asset(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    entity_type: EntityWithAssets,
    entity_id: int,
    asset_id: int,
) -> AssetRead:
    """Return the metadata of an assets associated with a specific entity."""
    return asset_service.get_entity_asset(
        repos,
        project_context=project_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )


@router.post("/{entity_type}/{entity_id}/assets", status_code=status.HTTP_201_CREATED)
def upload_entity_asset(
    *,
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    s3_client: S3ClientDep,
    entity_type: EntityWithAssets,
    entity_id: int,
    file: UploadFile,
    meta: Annotated[dict | None, Form()] = None,
) -> AssetRead:
    """Upload an asset to be associated with the specified entity.

    To be used only for small files. Use delegation for big files.
    """
    if not file.size or not validate_filesize(file.size):
        msg = f"File bigger than {settings.API_ASSET_POST_MAX_SIZE}, please use delegation"
        raise ApiError(message=msg, error_code=ApiErrorCode.INVALID_REQUEST)
    if not file.filename or not validate_filename(file.filename):
        msg = f"Invalid file name {file.filename!r}"
        raise ApiError(message=msg, error_code=ApiErrorCode.INVALID_REQUEST)
    content_type = get_content_type(file)
    asset_read = asset_service.create_entity_asset(
        repos=repos,
        project_context=project_context,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=file.filename,
        content_type=content_type,
        size=file.size,
        meta=meta,
    )
    if not upload_to_s3(
        s3_client,
        file_obj=file.file,
        bucket_name=asset_read.bucket_name,
        s3_key=asset_read.fullpath,
    ):
        raise HTTPException(status_code=500, detail="Failed to upload object")
    return asset_read


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    s3_client: S3ClientDep,
    entity_type: EntityWithAssets,
    entity_id: int,
    asset_id: int,
) -> RedirectResponse:
    asset = asset_service.get_entity_asset(
        repos,
        project_context=project_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    url = generate_presigned_url(
        s3_client=s3_client, bucket_name=asset.bucket_name, s3_key=asset.fullpath
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


@router.delete("/{entity_type}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    s3_client: S3ClientDep,
    entity_type: EntityWithAssets,
    entity_id: int,
    asset_id: int,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The asset record is not deleted from the database, but its status is changed.
    The file is actually deleted from S3, unless using a versioning-enabled bucket.
    """
    asset = asset_service.delete_entity_asset(
        repos,
        project_context=project_context,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )
    if not delete_from_s3(s3_client, bucket_name=asset.bucket_name, s3_key=asset.fullpath):
        raise HTTPException(status_code=500, detail="Failed to delete object")
    return AssetRead.model_validate(asset)


@router.post("/{entity_type}/{entity_id}/assets/upload/initiate")
def initiate_entity_asset_upload(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    entity_type: EntityWithAssets,
    entity_id: int,
):
    """Generate a signed URL with expiration that can be used to upload the file directly to S3."""
    raise NotImplementedError


@router.post("/{entity_type}/{entity_id}/assets/upload/complete")
def complete_entity_asset_upload(
    repos: RepoGroupDep,
    project_context: VerifiedProjectContextHeader,
    entity_type: EntityWithAssets,
    entity_id: int,
):
    """Register the uploaded file."""
    raise NotImplementedError
