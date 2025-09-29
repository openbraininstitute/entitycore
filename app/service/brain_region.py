import uuid

import sqlalchemy as sa

import app.queries.common
from app.db.model import BrainRegion
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.base import BrainRegionAdminUpdate, BrainRegionCreate, BrainRegionRead
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.utils.embedding import generate_embedding


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    brain_region_filter: BrainRegionFilterDep,
    semantic_search: str | None = None,
) -> ListResponse[BrainRegionRead]:
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
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_region_filter,
        embedding=embedding,
    )


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionRead.model_validate(row)


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    return read_one(db, id_)


def create_one(
    *,
    db: SessionDep,
    json_model: BrainRegionCreate,
    user_context: AdminContextDep,
) -> BrainRegionRead:
    embedding = generate_embedding(json_model.name)

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=BrainRegion,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=BrainRegionRead,
        embedding=embedding,
    )


def update_one(
    db: SessionDep,
    user_context: AdminContextDep,  # noqa: ARG001
    id_: uuid.UUID,
    json_model: BrainRegionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainRegionRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
        user_context=None,
        json_model=json_model,
        response_schema_class=BrainRegionRead,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: BrainRegionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> BrainRegionRead:
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
        user_context=None,
        json_model=json_model,
        response_schema_class=BrainRegionRead,
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
