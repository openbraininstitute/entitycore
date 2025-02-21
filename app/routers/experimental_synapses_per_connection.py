from fastapi import APIRouter, HTTPException

from app.db.auth import constrain_to_accessible_entities
from app.db.model import BrainLocation, ExperimentalSynapsesPerConnection
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)

router = APIRouter(
    prefix="/experimental_synapses_per_connection",
    tags=["experimental_synapses_per_connection"],
)


@router.get("/", response_model=list[ExperimentalSynapsesPerConnectionRead])
def read_experimental_neuron_densities(
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    return (
        constrain_to_accessible_entities(
            db.query(ExperimentalSynapsesPerConnection), project_context.project_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{experimental_synapses_per_connection_id}",
    response_model=ExperimentalSynapsesPerConnectionRead,
)
def read_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    experimental_synapses_per_connection_id: int,
    db: SessionDep,
):
    experimental_synapses_per_connection_id = (
        constrain_to_accessible_entities(
            db.query(ExperimentalSynapsesPerConnection),
            project_context.project_id,
        )
        .filter(ExperimentalSynapsesPerConnection.id == experimental_synapses_per_connection_id)
        .first()
    )

    if experimental_synapses_per_connection_id is None:
        raise HTTPException(
            status_code=404, detail="experimental_synapses_per_connection not found"
        )
    return ExperimentalSynapsesPerConnectionRead.model_validate(
        experimental_synapses_per_connection_id
    )


@router.post("/", response_model=ExperimentalSynapsesPerConnectionRead)
def create_experimental_neuron_density(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalSynapsesPerConnectionCreate,
    db: SessionDep,
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_neuron_density = ExperimentalSynapsesPerConnection(
        **dump, authorized_project_id=project_context.project_id
    )
    db.add(db_experimental_neuron_density)
    db.commit()
    db.refresh(db_experimental_neuron_density)
    return db_experimental_neuron_density
