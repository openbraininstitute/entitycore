from fastapi import APIRouter, HTTPException

from app.db.model import BrainLocation, ExperimentalSynapsesPerConnection
from app.dependencies.db import SessionDep
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)

router = APIRouter(
    prefix="/experimental_synapses_per_connection",
    tags=["experimental_synapses_per_connection"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ExperimentalSynapsesPerConnectionRead])
def read_experimental_neuron_densities(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(ExperimentalSynapsesPerConnection).offset(skip).limit(limit).all()


@router.get(
    "/{experimental_synapses_per_connection_id}",
    response_model=ExperimentalSynapsesPerConnectionRead,
)
def read_experimental_neuron_density(experimental_synapses_per_connection_id: int, db: SessionDep):
    experimental_synapses_per_connection_id = (
        db.query(ExperimentalSynapsesPerConnection)
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
    density: ExperimentalSynapsesPerConnectionCreate, db: SessionDep
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_neuron_density = ExperimentalSynapsesPerConnection(**dump)
    db.add(db_experimental_neuron_density)
    db.commit()
    db.refresh(db_experimental_neuron_density)
    return db_experimental_neuron_density
