import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Strain
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.base import StrainCreate, StrainRead

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)


@router.get("/", response_model=ListResponse[StrainRead])
def read_strains(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Strain)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[StrainRead](
        data=[StrainRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=StrainRead)
def read_strain(id_: int, db: SessionDep):
    with ensure_result(error_message="Strain not found"):
        stmt = sa.select(Strain).filter(Strain.id == id_)
        row = db.execute(stmt).scalar_one()
    return StrainRead.model_validate(row)


@router.post("/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: SessionDep):
    row = Strain(name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
