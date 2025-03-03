import sqlalchemy as sa
from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ExperimentalBoutonDensity
from app.dependencies import PaginationQuery
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.density import (
    ExperimentalBoutonDensityCreate,
    ExperimentalBoutonDensityRead,
)

router = APIRouter(
    prefix="/experimental-bouton-density",
    tags=["experimental-bouton-density"],
)


@router.get("", response_model=ListResponse[ExperimentalBoutonDensityRead])
def read_experimental_bouton_densities(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
):
    query = constrain_to_accessible_entities(
        sa.select(ExperimentalBoutonDensity), project_context.project_id
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[ExperimentalBoutonDensityRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=ExperimentalBoutonDensityRead)
def read_experimental_bouton_density(
    project_context: VerifiedProjectContextHeader,
    id_: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalBoutonDensity not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(ExperimentalBoutonDensity).filter(ExperimentalBoutonDensity.id == id_),
            project_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return ExperimentalBoutonDensityRead.model_validate(row)


@router.post("", response_model=ExperimentalBoutonDensityRead)
def create_experimental_bouton_density(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalBoutonDensityCreate,
    db: SessionDep,
):
    dump = density.model_dump()

    row = ExperimentalBoutonDensity(**dump, authorized_project_id=project_context.project_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
