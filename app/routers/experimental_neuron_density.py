import sqlalchemy as sa
from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ExperimentalNeuronDensity
from app.dependencies import PaginationQuery
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.density import (
    ExperimentalNeuronDensityCreate,
    ExperimentalNeuronDensityRead,
)

router = APIRouter(
    prefix="/experimental-neuron-density",
    tags=["experimental_neuron_density"],
)


@router.get("")
def read_experimental_neuron_densities(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
) -> ListResponse[ExperimentalNeuronDensityRead]:
    query = constrain_to_accessible_entities(
        sa.select(ExperimentalNeuronDensity), project_context.project_id
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(ExperimentalNeuronDensity.id))
    ).scalar_one()

    response = ListResponse[ExperimentalNeuronDensityRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=ExperimentalNeuronDensityRead)
def read_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    id_: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalNeuronDensity not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(ExperimentalNeuronDensity).filter(ExperimentalNeuronDensity.id == id_),
            project_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return ExperimentalNeuronDensityRead.model_validate(row)


@router.post("", response_model=ExperimentalNeuronDensityRead)
def create_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalNeuronDensityCreate,
    db: SessionDep,
):
    dump = density.model_dump()

    row = ExperimentalNeuronDensity(**dump, authorized_project_id=project_context.project_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
