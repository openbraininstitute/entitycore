import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends

from app.db.model import Strain
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.common import StrainFilter
from app.schemas.base import StrainCreate, StrainRead
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)


@router.get("")
def read_strains(
    db: SessionDep,
    pagination_request: PaginationQuery,
    strain_filter: Annotated[StrainFilter, FilterDepends(StrainFilter)],
) -> ListResponse[StrainRead]:
    query = sa.select(Strain)
    query = strain_filter.filter(query)
    total_items = db.execute(query.with_only_columns(sa.func.count(Strain.id))).scalar_one()

    query = strain_filter.sort(query)
    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    response = ListResponse[StrainRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=StrainRead)
def read_strain(id_: uuid.UUID, db: SessionDep):
    with ensure_result(error_message="Strain not found"):
        stmt = sa.select(Strain).filter(Strain.id == id_)
        row = db.execute(stmt).scalar_one()
    return StrainRead.model_validate(row)


@router.post("", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: SessionDep):
    row = Strain(name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
