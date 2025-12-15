import uuid

from fastapi import APIRouter

from app.db.utils import RESOURCE_TYPE_TO_CLASS
from app.dependencies.common import PaginationQuery
from app.dependencies.db import RepoGroupDep, SessionDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.filters.asset import AssetFilterDep
from app.queries.common import router_admin_delete_one
from app.schemas.asset import (
    AssetRead,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.service import admin as admin_service, asset as asset_service
from app.utils.routers import EntityRoute, ResourceRoute, entity_route_to_type, route_to_type

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    include_in_schema=False,
)


@router.delete("/{route}/{id_}")
def delete_one(
    db: SessionDep,
    route: ResourceRoute,
    id_: uuid.UUID,
) -> DeleteResponse:
    resource_type = route_to_type(route)
    return router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=RESOURCE_TYPE_TO_CLASS[resource_type],
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
    storage_client_factory: StorageClientFactoryDep,
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
        hard_delete=True,
    )
    asset_service.delete_asset_storage_object(asset, storage_client_factory)
    return asset
