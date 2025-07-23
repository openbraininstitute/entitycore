import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import Consortium
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.schemas.agent import ConsortiumCreate, ConsortiumRead
from app.schemas.types import ListResponse, PaginationResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Consortium.created_by, innerjoin=True),
        joinedload(Consortium.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[ConsortiumRead]:
    query = sa.select(Consortium)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(Consortium.id))).scalar_one()

    response = ListResponse[ConsortiumRead](
        data=[ConsortiumRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> ConsortiumRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Consortium,
        authorized_project_id=None,
        response_schema_class=ConsortiumRead,
        apply_operations=_load,
    )


def create_one(
    json_model: ConsortiumCreate, db: SessionDep, user_context: AdminContextDep
) -> ConsortiumRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Consortium,
        json_model=json_model,
        response_schema_class=ConsortiumRead,
        user_context=user_context,
        apply_operations=_load,
    )
