import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Species
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.base import SpeciesCreate, SpeciesRead

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get("/", response_model=ListResponse[SpeciesRead])
def get(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Species)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[SpeciesRead](
        data=[SpeciesRead.model_validate(d) for d in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=SpeciesRead)
def read_species(id_: int, db: SessionDep):
    with ensure_result(error_message="Species not found"):
        row = db.query(Species).filter(Species.id == id_).one()
    return SpeciesRead.model_validate(row)


@router.post("/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    row = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
