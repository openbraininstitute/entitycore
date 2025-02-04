"""Generic asset routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.types import EntityType
from app.dependencies.auth import ProjectDep
from app.dependencies.db import RepoGroupDep
from app.dependencies.s3 import S3ClientDep
from app.errors import ApiError, ApiErrorCode
from app.routers.types import ListResponse, Pagination
from app.schemas.asset import AssetRead
from app.service import asset as asset_service
from app.utils.s3 import (
    build_s3_path,
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
    repos: RepoGroupDep, proj_id: ProjectDep, entity_type: EntityType, entity_id: int
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    assets = asset_service.get_entity_assets(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
    )
    # TODO: proper pagination
    pagination = Pagination(page=1, page_size=len(assets), total_items=len(assets))
    return ListResponse[AssetRead](data=assets, pagination=pagination)


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}")
def get_entity_asset(
    repos: RepoGroupDep,
    proj_id: ProjectDep,
    entity_type: EntityType,
    entity_id: int,
    asset_id: UUID,
) -> AssetRead:
    """Return the metadata of an assets associated with a specific entity."""
    return asset_service.get_entity_asset(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
        asset_id=asset_id,
    )


@router.post("/{entity_type}/{entity_id}/assets", status_code=status.HTTP_201_CREATED)
def upload_entity_asset(
    repos: RepoGroupDep,
    proj_id: ProjectDep,
    s3_client: S3ClientDep,
    entity_type: EntityType,
    entity_id: int,
    file: UploadFile,
    meta: Annotated[dict | None, Form()] = None,
) -> AssetRead:
    """Upload an asset to be associated with the specified entity.

    To be used only for small files. Use delegation for big files.
    """
    if not validate_filesize(file.size):
        msg = f"File bigger than {settings.API_ASSET_POST_MAX_SIZE}, please use delegation"
        raise ApiError(message=msg, error_code=ApiErrorCode.INVALID_REQUEST)
    if not validate_filename(file.filename):
        msg = f"Invalid file name {file.filename}"
        raise ApiError(message=msg, error_code=ApiErrorCode.INVALID_REQUEST)
    bucket_name = settings.S3_PRIVATE_BUCKET_NAME
    asset_path = build_s3_path(proj_id, entity_type, entity_id, file.filename)
    asset = repos.asset.create_entity_asset(
        entity_type=entity_type,
        entity_id=entity_id,
        path=asset_path,
        is_directory=False,
        is_public=False,
        content_type=file.content_type,
        size=file.size,
        meta=meta or {},
    )
    if not upload_to_s3(s3_client, file_obj=file.file, bucket_name=bucket_name, s3_key=asset_path):
        raise HTTPException(status_code=500, detail="Failed to upload object")
    return AssetRead.model_validate(asset)


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep,
    proj_id: ProjectDep,
    s3_client: S3ClientDep,
    entity_type: EntityType,
    entity_id: int,
    asset_id: UUID,
) -> RedirectResponse:
    asset = asset_service.get_entity_asset(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
        asset_id=asset_id,
    )
    bucket_name = settings.S3_PRIVATE_BUCKET_NAME
    url = generate_presigned_url(s3_client=s3_client, bucket_name=bucket_name, s3_key=asset.path)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned url")
    return RedirectResponse(url=url)


@router.delete("/{entity_type}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    proj_id: ProjectDep,
    s3_client: S3ClientDep,
    entity_type: EntityType,
    entity_id: int,
    asset_id: UUID,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The asset record is not deleted from the database, but its status is changed.
    The file is actually deleted from S3, unless using a versioning-enabled bucket.
    """
    # TODO:
    #  - what if the user want to re-upload the same file that was deleted?
    asset = asset_service.delete_entity_asset(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
        asset_id=asset_id,
    )
    bucket_name = settings.S3_PRIVATE_BUCKET_NAME
    if not delete_from_s3(s3_client, bucket_name=bucket_name, s3_key=asset.path):
        raise HTTPException(status_code=500, detail="Failed to delete object")
    return AssetRead.model_validate(asset)


@router.post("/{entity_type}/{entity_id}/assets/upload/initiate")
def initiate_entity_asset_upload(
    repos: RepoGroupDep, proj_id: ProjectDep, entity_type: EntityType, entity_id: int
):
    """Generate a signed URL with expiration that can be used to upload the file directly to S3."""
    raise NotImplementedError


@router.post("/{entity_type}/{entity_id}/assets/upload/complete")
def complete_entity_asset_upload(
    repos: RepoGroupDep, proj_id: ProjectDep, entity_type: EntityType, entity_id: int
):
    """Register the uploaded file."""
    raise NotImplementedError
