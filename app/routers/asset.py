"""Generic asset routes."""

from uuid import UUID

from fastapi import APIRouter
from starlette.responses import FileResponse

from app.db.types import EntityType
from app.dependencies.db import RepoGroupDep
from app.schemas.asset import AssetRead
from app.service import asset as asset_service

router = APIRouter(
    prefix="",
    tags=["assets"],
)


@router.get("/{entity_type}/{entity_id}/assets")
def get_entity_assets(repos: RepoGroupDep, entity_type: EntityType, entity_id: int) -> dict:
    """Return the list of assets associated with a specific entity."""
    proj_id: UUID = UUID("00000000-0000-0000-0000-000000000001")  # FIXME: to be read from headers
    assets = asset_service.get_entity_assets(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
    )
    # TODO: pagination
    return {
        "results": assets,
    }


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}")
def get_entity_asset(
    repos: RepoGroupDep, entity_type: EntityType, entity_id: int, asset_id: UUID
) -> AssetRead:
    """Return the metadata of an assets associated with a specific entity."""
    proj_id: UUID = UUID("00000000-0000-0000-0000-000000000001")  # FIXME: to be read from headers
    return asset_service.get_entity_asset(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
        asset_id=asset_id,
    )


@router.post("/{entity_type}/{entity_id}/assets")
def upload_entity_asset(repos: RepoGroupDep, entity_type: EntityType, entity_id: int) -> AssetRead:
    """Upload an asset to be associated with the specified entity."""
    # TODO:
    #  - to be used only for small files, and use delegation for big files
    #  - what if the user want to overwrite an existing file?
    raise NotImplementedError


@router.get("/{entity_type}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep, entity_type: EntityType, entity_id: int, asset_id: UUID
) -> FileResponse:
    # TODO: check authn/authz, retrieve the asset metadata, stream the content, or return a redirect
    file_path = "pyproject.toml"
    return FileResponse(file_path)


@router.delete("/{entity_type}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep, entity_type: EntityType, entity_id: int, asset_id: UUID
) -> AssetRead:
    """Delete the data and metadata of an assets associated with a specific entity."""
    # TODO:
    #  - should we keep the asset record, but mark it as deleted?
    #  - should we keep or delete the asset in the datastore?
    #  - what if the user want to re-upload the same file that was deleted?
    proj_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    return asset_service.delete_entity_asset(
        repos,
        entity_type=entity_type,
        entity_id=entity_id,
        proj_id=proj_id,
        asset_id=asset_id,
    )


@router.post("/{entity_type}/{entity_id}/assets/upload/initiate")
def initiate_entity_asset_upload(repos: RepoGroupDep, entity_type: EntityType, entity_id: int):
    """Generate a signed URL with expiration that can be used to upload the file directly to S3."""
    raise NotImplementedError


@router.post("/{entity_type}/{entity_id}/assets/upload/complete")
def complete_entity_asset_upload(repos: RepoGroupDep, entity_type: EntityType, entity_id: int):
    """Register the uploaded file."""
    raise NotImplementedError
