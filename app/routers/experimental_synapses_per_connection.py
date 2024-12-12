from fastapi import APIRouter
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionRead,
    ExperimentalSynapsesPerConnectionCreate,
)
from app.models.density import ExperimentalSynapsesPerConnection
from app.models.base import BrainLocation
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from typing import List
from app.dependencies.db import get_db

router = APIRouter(
    prefix="/experimental_synapses_per_connection",
    tags=["experimental_synapses_per_connection"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{experimental_synapses_per_connection_id}",
    response_model=ExperimentalSynapsesPerConnectionRead,
)
async def read_experimental_neuron_density(
    experimental_synapses_per_connection_id: int, db: Session = Depends(get_db)
):
    experimental_synapses_per_connection_id= (
        db.query(ExperimentalSynapsesPerConnection)
        .filter(ExperimentalSynapsesPerConnection.id == experimental_synapses_per_connection_id)
        .first()
    )

    if experimental_synapses_per_connection_id is None:
        raise HTTPException(
            status_code=404, detail="experimental_synapses_per_connection not found"
        )
    ret = ExperimentalSynapsesPerConnectionRead.model_validate(experimental_synapses_per_connection_id)
    return ret


@router.post("/", response_model=ExperimentalSynapsesPerConnectionRead)
def create_experimental_neuron_density(
    density: ExperimentalSynapsesPerConnectionCreate, db: Session = Depends(get_db)
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_neuron_density = ExperimentalSynapsesPerConnection(**dump)
    db.add(db_experimental_neuron_density)
    db.commit()
    db.refresh(db_experimental_neuron_density)
    return db_experimental_neuron_density


@router.get("/", response_model=List[ExperimentalSynapsesPerConnectionRead])
async def read_experimental_neuron_density(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(ExperimentalSynapsesPerConnection).offset(skip).limit(limit).all()
    return users
