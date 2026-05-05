import uuid
from typing import Annotated

from fastapi import APIRouter, Form, Query, UploadFile, status
from starlette.responses import RedirectResponse

from app.config import storages
from app.db.types import AssetLabel, StorageType
from app.dependencies.auth import AdminContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import RepoGroupDep, SessionDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.filters.asset import AssetFilterDep
from app.routers.types import EntityRoute
from app.schemas.asset import (
    AssetRead,
)
from app.schemas.publish import ChangeProjectVisibilityResponse
from app.schemas.types import ListResponse
from app.service import (
    admin as admin_service,
    asset as asset_service,
    publish as publish_service,
)
from app.utils.routers import (
    entity_route_to_type,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    include_in_schema=False,
)


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}")
def get_entity_asset(
    repos: RepoGroupDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    return admin_service.get_entity_asset(
        repos=repos,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )


@router.get("/{entity_route}/{entity_id}/assets")
def get_entity_assets(
    repos: RepoGroupDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: AssetFilterDep,
) -> ListResponse[AssetRead]:
    return admin_service.get_entity_assets(
        repos=repos,
        entity_route=entity_route,
        entity_id=entity_id,
        pagination_request=pagination_request,
        filter_model=filter_model,
    )


@router.delete("/{entity_route}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Delete an assets associated with a specific entity.

    The asset record is not deleted from the database, but its status is changed.
    The file is actually deleted from S3, unless it's stored in open data storage.
    """
    asset = asset_service.delete_asset(
        repos,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    # Note: Asset storage object is deleted via app.db.events
    return asset


@router.get("/{entity_route}/{entity_id}/assets/{asset_id}/download")
def download_entity_asset(
    repos: RepoGroupDep,
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
    return admin_service.download_entity_asset(
        repos=repos,
        storage_client_factory=storage_client_factory,
        entity_route=entity_route,
        entity_id=entity_id,
        asset_id=asset_id,
        asset_path=asset_path,
    )


@router.post("/{entity_route}/{entity_id}/assets", status_code=status.HTTP_201_CREATED)
def upload_entity_asset(
    *,
    repos: RepoGroupDep,
    user_context: AdminContextWithProjectIdDep,
    storage_client_factory: StorageClientFactoryDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    file: UploadFile,
    label: Annotated[AssetLabel, Form()],
    meta: Annotated[dict | None, Form()] = None,
) -> AssetRead:
    return admin_service.upload_entity_asset(
        repos=repos,
        user_context=user_context,
        storage_client_factory=storage_client_factory,
        entity_route=entity_route,
        entity_id=entity_id,
        file=file,
        label=label,
        meta=meta,
    )


@router.post("/publish-project/{project_id}")
def publish_project(
    db: SessionDep,
    storage_client_factory: StorageClientFactoryDep,
    *,
    project_id: uuid.UUID,
    max_assets: Annotated[
        int | None, Query(description="Limit the number of assets to be made public.")
    ] = None,
    dry_run: Annotated[
        bool, Query(description="Simulate the operation without making any change.")
    ],
) -> ChangeProjectVisibilityResponse:
    """Publish the content of a project.

    This endpoint is used to make public the resources in a project.

    It's recommended to call the endpoint with dry_run=true before running it with dry_run=false.

    If max_assets is specified, the endpoint should be called multiple times until the response
    says that the operation is completed.
    """
    storage = storages[StorageType.aws_s3_internal]
    s3_client = storage_client_factory(storage)
    return publish_service.set_project_visibility(
        db=db,
        s3_client=s3_client,
        project_id=project_id,
        storage=storage,
        max_assets=max_assets,
        dry_run=dry_run,
        public=True,
    )


@router.post("/unpublish-project/{project_id}")
def unpublish_project(
    db: SessionDep,
    storage_client_factory: StorageClientFactoryDep,
    project_id: uuid.UUID,
    *,
    max_assets: Annotated[
        int | None, Query(description="Limit the number of assets to be made private.")
    ] = None,
    dry_run: bool,
) -> ChangeProjectVisibilityResponse:
    """Unpublish the content of a project.

    This endpoint is used to make private the resources in a project.

    It's recommended to call the endpoint with dry_run=true before running it with dry_run=false.

    If max_assets is specified, the endpoint should be called multiple times until the response
    says that the operation is completed.
    """
    storage = storages[StorageType.aws_s3_internal]
    s3_client = storage_client_factory(storage)
    return publish_service.set_project_visibility(
        db=db,
        s3_client=s3_client,
        project_id=project_id,
        storage=storage,
        max_assets=max_assets,
        dry_run=dry_run,
        public=False,
    )
