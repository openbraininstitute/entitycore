import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import BrainRegion, BrainRegionHierarchy, Species, Strain
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.brain_region import BrainRegionFilterDep
from app.schemas.brain_region import BrainRegionAdminUpdate, BrainRegionCreate, BrainRegionRead
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
) -> ListResponse[BrainRegionRead]:
    db_model_class = BrainRegion
    filter_joins = {
        "species": lambda q: q.join(
            BrainRegionHierarchy, db_model_class.hierarchy_id == BrainRegionHierarchy.id
        ).join(Species, BrainRegionHierarchy.species_id == Species.id),
        "strain": lambda q: q.join(
            BrainRegionHierarchy, db_model_class.hierarchy_id == BrainRegionHierarchy.id
        ).join(Strain, BrainRegionHierarchy.strain_id == Species.id),
    }

    return app.queries.common.router_read_many(
        db=db,
        db_model_class=db_model_class,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=BrainRegionRead,
        name_to_facet_query_params=None,
        filter_model=brain_region_filter,
        filter_joins=filter_joins,
        embedding=None if semantic_search is None else generate_embedding(semantic_search),
    )


def read_one(db: SessionDep, id_: uuid.UUID) -> BrainRegionRead:
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(_load(stmt)).scalar_one()
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
        apply_operations=_load,
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
        apply_operations=_load,
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
        apply_operations=_load,
    )


def delete_one(
    db: SessionDep,
    id_: uuid.UUID,
    user_context: AdminContextDep,  # noqa: ARG001
) -> DeleteResponse:
    return app.queries.common.router_admin_delete_one(
        id_=id_,
        db=db,
        db_model_class=BrainRegion,
    )
