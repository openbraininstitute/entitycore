import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload, selectinload

import app.queries.common
from app.db.model import BrainAtlas, BrainAtlasRegion
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.brain_atlas import BrainAtlasFilterDep, BrainAtlasRegionFilterDep
from app.schemas.brain_atlas import (
    BrainAtlasAdminUpdate,
    BrainAtlasCreate,
    BrainAtlasRead,
    BrainAtlasUpdate,
)
from app.schemas.brain_atlas_region import BrainAtlasRegionRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load_brain_atlas(query: sa.Select):
    return query.options(
        joinedload(BrainAtlas.created_by),
        joinedload(BrainAtlas.updated_by),
        joinedload(BrainAtlas.species),
        joinedload(BrainAtlas.strain),
        selectinload(BrainAtlas.assets),
        raiseload("*"),
    )


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
        apply_data_query_operations=_load_brain_atlas,
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
        user_context=user_context,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def admin_read_one(db: SessionDep, atlas_id: uuid.UUID) -> BrainAtlasRead:
    return app.queries.common.router_read_one(
        id_=atlas_id,
        db=db,
        db_model_class=BrainAtlas,
        user_context=None,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def create_one(
    db: SessionDep,
    json_model: BrainAtlasCreate,
    user_context: UserContextWithProjectIdDep,
) -> BrainAtlasRead:
    return app.queries.common.router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=BrainAtlas,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainAtlasUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainAtlasRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainAtlasAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainAtlasRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=None,
        json_model=json_model,
        response_schema_class=BrainAtlasRead,
        apply_operations=_load_brain_atlas,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return app.queries.common.router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=BrainAtlas,
        user_context=user_context,
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
        user_context=user_context,
        response_schema_class=BrainAtlasRegionRead,
        apply_operations=lambda select: select.filter(
            BrainAtlasRegion.brain_atlas_id == atlas_id
        ).options(selectinload(BrainAtlasRegion.assets)),
    )
