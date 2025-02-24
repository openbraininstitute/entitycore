from fastapi import APIRouter

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


@router.get("/", response_model=list[ExperimentalNeuronDensityRead])
def read_experimental_neuron_densities(
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    return (
        constrain_to_accessible_entities(
            db.query(ExperimentalNeuronDensity), project_context.project_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


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
