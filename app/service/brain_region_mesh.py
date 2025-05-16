import uuid

from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import BrainRegion, Mesh as BrainRegionMesh
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetQueryParams,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.brain_region_mesh import BrainRegionMeshFilterDep
from app.queries import facets as fc
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.brain_region_mesh import BrainRegionMeshCreate, BrainRegionMeshRead
from app.schemas.types import ListResponse


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> BrainRegionMeshRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=BrainRegionMesh,
        authorized_project_id=user_context.project_id,
        response_schema_class=BrainRegionMeshRead,
        apply_operations=lambda q: q.options(
            joinedload(BrainRegionMesh.brain_region),
            joinedload(BrainRegionMesh.assets),
            raiseload("*"),
        ),
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: BrainRegionMeshCreate,
    db: SessionDep,
) -> BrainRegionMeshRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=BrainRegionMesh,
        authorized_project_id=user_context.project_id,
        response_schema_class=BrainRegionMeshRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: BrainRegionMeshFilterDep,
    with_search: SearchDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[BrainRegionMeshRead]:
    name_to_facet_query_params: dict[str, FacetQueryParams] = fc.brain_region
    apply_filter_query = lambda query: (
        query.join(BrainRegion, BrainRegionMesh.brain_region_id == BrainRegion.id)
    )
    apply_data_options = lambda query: (
        query.options(joinedload(BrainRegionMesh.brain_region))
        .options(selectinload(BrainRegionMesh.assets))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=BrainRegionMesh,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_options,
        aliases={},
        pagination_request=pagination_request,
        response_schema_class=BrainRegionMeshRead,
        authorized_project_id=user_context.project_id,
    )
