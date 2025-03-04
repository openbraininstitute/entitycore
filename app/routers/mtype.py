import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import MTypeClass
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.mtype import MTypeClassRead

router = APIRouter(
    prefix="/mtype",
    tags=["mtype"],
)


@router.get("/", response_model=ListResponse[MTypeClassRead])
def read_mtypes(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(MTypeClass)

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[MTypeClassRead](
        data=[MTypeClassRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=MTypeClassRead)
def read_mtype(id_: int, db: SessionDep):
    with ensure_result(error_message="MTypeClass not found"):
        stmt = sa.select(MTypeClass).filter(MTypeClass.id == id_)
        row = db.execute(stmt).scalar_one()
    return MTypeClassRead.model_validate(row)
