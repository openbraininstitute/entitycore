import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends

from app.db.model import Species
from app.dependencies.auth import user_with_service_admin_role
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.common import SpeciesFilter
from app.schemas.base import SpeciesCreate, SpeciesRead
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get("")
def get(
    db: SessionDep,
    pagination_request: PaginationQuery,
    species_filter: Annotated[SpeciesFilter, FilterDepends(SpeciesFilter)],
) -> ListResponse[SpeciesRead]:
    query = sa.select(Species)
    query = species_filter.filter(query)
    total_items = db.execute(query.with_only_columns(sa.func.count(Species.id))).scalar_one()

    query = species_filter.sort(query)
    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    response = ListResponse[SpeciesRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=SpeciesRead)
def read_species(id_: uuid.UUID, db: SessionDep):
    with ensure_result(error_message="Species not found"):
        stmt = sa.select(Species).filter(Species.id == id_)
        row = db.execute(stmt).scalar_one()
    return SpeciesRead.model_validate(row)


@router.post("", dependencies=[Depends(user_with_service_admin_role)], response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    row = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
