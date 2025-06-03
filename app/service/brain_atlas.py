import uuid

from sqlalchemy.orm import selectinload

import app.queries.common
from app.db.model import BrainAtlas, BrainAtlasRegion
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.brain_atlas import BrainAtlasFilterDep, BrainAtlasRegionFilterDep
from app.schemas.brain_atlas import BrainAtlasRead, BrainAtlasRegionRead
from app.schemas.types import ListResponse


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_filter: BrainAtlasFilterDep,
) -> ListResponse[BrainAtlasRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlas,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=lambda select: select.options(selectinload(BrainAtlas.assets)),
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRead,
        name_to_facet_query_params=None,
        filter_model=brain_atlas_filter,
    )


def read_one(user_context: UserContextDep, atlas_id: uuid.UUID, db: SessionDep) -> BrainAtlasRead:
    return app.queries.common.router_read_one(
        id_=atlas_id,
        db=db,
        db_model_class=BrainAtlas,
        authorized_project_id=user_context.project_id,
        response_schema_class=BrainAtlasRead,
        apply_operations=lambda select: select.options(selectinload(BrainAtlas.assets)),
    )


def read_many_region(
    user_context: UserContextDep,
    atlas_id: uuid.UUID,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_region_filter: BrainAtlasRegionFilterDep,
) -> ListResponse[BrainAtlasRegionRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlasRegion,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=lambda q: q.filter(
            BrainAtlasRegion.brain_atlas_id == atlas_id
        ),
        apply_data_query_operations=lambda s: s.options(selectinload(BrainAtlasRegion.assets)),
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_atlas_region_filter,
    )


def read_one_region(
    user_context: UserContextDep, atlas_id: uuid.UUID, atlas_region_id: uuid.UUID, db: SessionDep
) -> BrainAtlasRegionRead:
    return app.queries.common.router_read_one(
        id_=atlas_region_id,
        db=db,
        db_model_class=BrainAtlasRegion,
        authorized_project_id=user_context.project_id,
        response_schema_class=BrainAtlasRegionRead,
        apply_operations=lambda select: select.filter(
            BrainAtlasRegion.brain_atlas_id == atlas_id
        ).options(selectinload(BrainAtlasRegion.assets)),
    )
