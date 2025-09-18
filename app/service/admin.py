import uuid

from app.db.model import Asset, Entity
from app.db.types import EntityType
from app.dependencies.common import PaginationQuery
from app.errors import ApiErrorCode, ensure_result
from app.filters.asset import AssetFilterDep
from app.queries.common import router_read_many
from app.repository.group import RepositoryGroup
from app.schemas.asset import (
    AssetRead,
)
from app.schemas.types import ListResponse
from app.utils.routers import EntityRoute, entity_route_to_type


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
