import uuid

import sqlalchemy as sa

import app.queries.common
from app.db.model import Strain
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.common import StrainFilterDep
from app.schemas.base import StrainCreate, StrainRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    strain_filter: StrainFilterDep,
) -> ListResponse[StrainRead]:
    query = sa.select(Strain)
    query = strain_filter.filter(query)
    total_items = db.execute(query.with_only_columns(sa.func.count(Strain.id))).scalar_one()

    query = strain_filter.sort(query)
    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    response = ListResponse[StrainRead](
        data=[StrainRead.model_validate(row) for row in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> StrainRead:
    with ensure_result(error_message="Strain not found"):
        stmt = sa.select(Strain).filter(Strain.id == id_)
        row = db.execute(stmt).scalar_one()
    return StrainRead.model_validate(row)


def create_one(
    json_model: StrainCreate, db: SessionDep, user_context: AdminContextDep
) -> StrainRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Strain,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=StrainRead,
    )
