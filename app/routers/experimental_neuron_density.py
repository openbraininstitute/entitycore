from app.routers.types import ListResponse, PaginationResponse
import sqlalchemy as sa
from fastapi import APIRouter
from app.dependencies import PaginationQuery

from app.db.auth import constrain_to_accessible_entities
from app.db.model import BrainLocation, ExperimentalNeuronDensity
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.density import (
    ExperimentalNeuronDensityCreate,
    ExperimentalNeuronDensityRead,
)

router = APIRouter(
    prefix="/experimental-neuron-density",
    tags=["experimental_neuron_density"],
)


@router.get("/", response_model=ListResponse[ExperimentalNeuronDensityRead])
def read_experimental_neuron_densities(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
):
    query = constrain_to_accessible_entities(
            sa.select(ExperimentalNeuronDensity), project_context.project_id
        )

    data = db.execute(
        query
        .offset(pagination_request.page * pagination_request.page_size)
        .limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

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


@router.get(
    "/{experimental_neuron_density_id}",
    response_model=ExperimentalNeuronDensityRead,
)
def read_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    experimental_neuron_density_id: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalNeuronDensity not found"):
        row = (
            constrain_to_accessible_entities(
                db.query(ExperimentalNeuronDensity), project_context.project_id
            )
            .filter(ExperimentalNeuronDensity.id == experimental_neuron_density_id)
            .one()
        )

    return row


@router.post("/", response_model=ExperimentalNeuronDensityRead)
def create_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalNeuronDensityCreate,
    db: SessionDep,
):
    dump = density.model_dump()

    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_neuron_density = ExperimentalNeuronDensity(
        **dump, authorized_project_id=project_context.project_id
    )
    db.add(db_experimental_neuron_density)
    db.commit()
    db.refresh(db_experimental_neuron_density)
    return db_experimental_neuron_density
