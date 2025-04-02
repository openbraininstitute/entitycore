import uuid

import sqlalchemy as sa

from app.db.model import Person
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.agent import PersonCreate, PersonRead
from app.schemas.types import ListResponse, PaginationResponse


def read_many(db: SessionDep, pagination_request: PaginationQuery) -> ListResponse[PersonRead]:
    query = sa.select(Person)

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
    with ensure_result(error_message="Person not found"):
        stmt = sa.select(Person).filter(Person.id == id_)
        row = db.execute(stmt).scalar_one()
    return PersonRead.model_validate(row)


def create_one(person: PersonCreate, db: SessionDep) -> PersonRead:
    row = Person(**person.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return PersonRead.model_validate(row)
