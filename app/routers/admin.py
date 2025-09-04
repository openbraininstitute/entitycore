import uuid

from fastapi import APIRouter

from app.db.utils import RESOURCE_TYPE_TO_CLASS
from app.dependencies.auth import AdminContextDep
from app.dependencies.db import RepoGroupDep, SessionDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.queries.common import router_delete_one
from app.schemas.asset import (
    AssetRead,
)
from app.service import asset as asset_service
from app.utils.routers import EntityRoute, ResourceRoute, entity_route_to_type, route_to_type

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.delete("/{route}/{id_}")
def delete_one(
    _: AdminContextDep,
    db: SessionDep,
    route: ResourceRoute,
    id_: uuid.UUID,
):
    resource_type = route_to_type(route)
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=RESOURCE_TYPE_TO_CLASS[resource_type],
        authorized_project_id=None,
    )


@router.delete("/{entity_route}/{entity_id}/assets/{asset_id}")
def delete_entity_asset(
    repos: RepoGroupDep,
    user_context: AdminContextDep,  # noqa: ARG001
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
