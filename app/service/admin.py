import uuid

from starlette.responses import RedirectResponse

from app.db.model import Asset, Entity
from app.db.types import EntityType
from app.db.utils import RESOURCE_TYPE_TO_CLASS
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiErrorCode, ensure_result
from app.filters.asset import AssetFilterDep
from app.queries.common import router_admin_delete_one, router_read_many
from app.repository.group import RepositoryGroup
from app.routers.types import EntityRoute, ResourceRoute
from app.schemas.asset import (
    AssetRead,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.service.asset import create_asset_download_redirect
from app.utils.routers import entity_route_to_type, route_to_type
from app.utils.s3 import StorageClientFactory


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


def get_entity_asset(
    repos: RepositoryGroup,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRead:
    """Return an asset associated with a specific entity."""
    with ensure_result(f"Asset {asset_id} not found", error_code=ApiErrorCode.ASSET_NOT_FOUND):
        asset = repos.asset.get_entity_asset(
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            include_deleted=True,
        )
    return AssetRead.model_validate(asset)


def get_entity_assets(
    repos: RepositoryGroup,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    filter_model: AssetFilterDep,
) -> ListResponse[AssetRead]:
    """Return the list of assets associated with a specific entity."""
    db_model_class = Asset
    entity_type = entity_route_to_type(entity_route)
    apply_filter_query_operations = lambda q: q.join(Entity, Entity.id == Asset.entity_id).where(
        Asset.entity_id == entity_id,
        Entity.type == entity_type.name,
    )
    name_to_facet_query_params = filter_joins = None
    return router_read_many(
        db=repos.db,
        db_model_class=db_model_class,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases={},
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=AssetRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )


def download_entity_asset(
    repos: RepositoryGroup,
    storage_client_factory: StorageClientFactory,
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
    asset = get_entity_asset(
        repos,
        entity_type=entity_route_to_type(entity_route),
        entity_id=entity_id,
        asset_id=asset_id,
    )
    return create_asset_download_redirect(
        asset=asset,
        storage_client_factory=storage_client_factory,
        asset_path=asset_path,
    )
