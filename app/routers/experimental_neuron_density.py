from fastapi import APIRouter
from app.schemas.density import (
    ExperimentalNeuronDensityRead,
    ExperimentalNeuronDensityCreate,
)
from app.models.density import ExperimentalNeuronDensity
from app.models.base import BrainLocation
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from typing import List
from app.dependencies.db import get_db

router = APIRouter(
    prefix="/experimental_neuron_density",
    tags=["experimental_neuron_density"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{experimental_neuron_density_id}",
    response_model=ExperimentalNeuronDensityRead,
)
async def read_experimental_neuron_density(
    experimental_neuron_density_id: int, db: Session = Depends(get_db)
):
    experimental_neuron_density = (
        db.query(ExperimentalNeuronDensity)
        .filter(ExperimentalNeuronDensity.id == experimental_neuron_density_id)
        .first()
    )

    if experimental_neuron_density is None:
        raise HTTPException(
            status_code=404, detail="experimental_neuron_density not found"
        )
    ret = ExperimentalNeuronDensityRead.model_validate(experimental_neuron_density)
    return ret


@router.post("/", response_model=ExperimentalNeuronDensityRead)
def create_experimental_neuron_density(
    density: ExperimentalNeuronDensityCreate, db: Session = Depends(get_db)
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.dict())

    db_experimental_neuron_density = ExperimentalNeuronDensity(**dump)
    db.add(db_experimental_neuron_density)
    db.commit()
    db.refresh(db_experimental_neuron_density)
    return db_experimental_neuron_density


@router.get("/", response_model=List[ExperimentalNeuronDensityRead])
async def read_experimental_neuron_density(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(ExperimentalNeuronDensity).offset(skip).limit(limit).all()
    return users
