import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Species
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.base import (
    SpeciesCreate,
)
from app.schemas.morphology import (
    SpeciesRead,
)

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get("/", response_model=ListResponse[SpeciesRead])
def read_role(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Species)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

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


@router.get("/{role_id}", response_model=SpeciesRead)
def read_person(role_id: int, db: SessionDep):
    with ensure_result(error_message="Species not found"):
        row = db.query(Species).filter(Species.id == role_id).one()
    return row


@router.post("/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    db_species = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species
