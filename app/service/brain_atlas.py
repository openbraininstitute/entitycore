import uuid

import sqlalchemy as sa

import app.queries.common
from app.db.model import BrainAtlas, BrainAtlasRegion
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_atlas import BrainAtlasFilterDep, BrainAtlasRegionFilterDep
from app.schemas.brain_atlas import BrainAtlasRead, BrainAtlasRegionRead
from app.schemas.types import ListResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_filter: BrainAtlasFilterDep,
) -> ListResponse[BrainAtlasRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlas,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRead,
        name_to_facet_query_params=None,
        filter_model=brain_atlas_filter,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> BrainAtlasRead:
    with ensure_result(error_message="Brain Atlas not found"):
        stmt = sa.select(BrainAtlas).filter(BrainAtlas.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainAtlasRead.model_validate(row)


def read_many_region(
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_atlas_region_filter: BrainAtlasRegionFilterDep,
) -> ListResponse[BrainAtlasRegionRead]:
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainAtlasRegion,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainAtlasRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_atlas_region_filter,
    )


def read_one_region(id_: uuid.UUID, region_id: uuid.UUID, db: SessionDep) -> BrainAtlasRegionRead:
    with ensure_result(error_message="Brain Atlas Region not found"):
        stmt = sa.select(BrainAtlasRegion).filter(
            sa.and_(BrainAtlasRegion.brain_atlas_id == id_, BrainAtlasRegion.id == region_id)
        )
        row = db.execute(stmt).scalar_one()
    return BrainAtlasRegionRead.model_validate(row)
