import sqlalchemy as sa
from fastapi import APIRouter

from app.db.model import Strain
from app.dependencies import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.base import (
    StrainCreate,
)
from app.schemas.morphology import (
    StrainRead,
)

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)


@router.get("/", response_model=ListResponse[StrainRead])
def read_organizations(db: SessionDep, pagination_request: PaginationQuery):
    query = sa.select(Strain)

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

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


@router.get("/{organization_id}", response_model=StrainRead)
def read_organization(organization_id: int, db: SessionDep):
    with ensure_result(error_message="Strain not found"):
        row = db.query(Strain).filter(Strain.id == organization_id).one()
    return row


@router.post("/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: SessionDep):
    db_strain = Strain(
        name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id
    )
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain
