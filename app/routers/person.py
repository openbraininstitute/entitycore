import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Person
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.agent import PersonCreate, PersonRead

router = APIRouter(
    prefix="/person",
    tags=["person"],
)


@router.get("/", response_model=ListResponse[PersonRead])
def read_persons(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Person)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[PersonRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=PersonRead)
def read_person(id_: int, db: SessionDep):
    with ensure_result(error_message="Person not found"):
        row = db.query(Person).filter(Person.id == id_).one()

    return PersonRead.model_validate(row)


@router.post("/", response_model=PersonRead)
def create_person(person: PersonCreate, db: SessionDep):
    row = Person(**person.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
