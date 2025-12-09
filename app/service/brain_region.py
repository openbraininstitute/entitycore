import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import BrainRegion
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.brain_region import BrainRegionAdminUpdate, BrainRegionCreate, BrainRegionReadFull
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.utils.embedding import generate_embedding


def _load(select: sa.Select):
    return select.options(
        joinedload(BrainRegion.species),
        joinedload(BrainRegion.strain),
        raiseload("*"),
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_filter: BrainRegionFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[BrainRegionReadFull]:
    embedding = None

    if semantic_search is not None:
        embedding = generate_embedding(semantic_search)

    return app.queries.common.router_read_many(
        db=db,
        db_model_class=BrainRegion,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionReadFull,
        name_to_facet_query_params=None,
        filter_model=brain_region_filter,
        embedding=embedding,
    )


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionReadFull:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(_load(stmt)).scalar_one()
    return BrainRegionReadFull.model_validate(row)


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionReadFull:
    return read_one(db, id_)


def create_one(
    *,
    db: SessionDep,
    json_model: BrainRegionCreate,
    user_context: AdminContextDep,
) -> BrainRegionReadFull:
    embedding = generate_embedding(json_model.name)

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=BrainRegion,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainRegionReadFull,
        apply_operations=_load,
        embedding=embedding,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: BrainRegionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainRegionReadFull:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
        user_context=None,
        json_model=json_model,
        response_schema_class=BrainRegionReadFull,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainRegionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainRegionReadFull:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
        user_context=None,
        json_model=json_model,
        response_schema_class=BrainRegionReadFull,
        apply_operations=_load,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return app.queries.common.router_delete_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
        user_context=None,
    )
