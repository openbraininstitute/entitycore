import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

import app.queries.common
from app.db.model import Person
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.schemas.agent import PersonCreate, PersonRead
from app.schemas.types import ListResponse, PaginationResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Person.created_by, innerjoin=True),
        joinedload(Person.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(db: SessionDep, pagination_request: PaginationQuery) -> ListResponse[PersonRead]:
    query = _load(sa.select(Person))

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count(Person.id))).scalar_one()

    response = ListResponse[PersonRead](
        data=[PersonRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


def read_one(id_: uuid.UUID, db: SessionDep) -> PersonRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Person,
        authorized_project_id=None,
        response_schema_class=PersonRead,
        apply_operations=_load,
    )


def create_one(person: PersonCreate, db: SessionDep, user_context: AdminContextDep) -> PersonRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Person,
        json_model=person,
        response_schema_class=PersonRead,
        user_context=user_context,
        apply_operations=_load,
    )
