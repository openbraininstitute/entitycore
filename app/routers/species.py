from fastapi import APIRouter

from app.db.model import Species
from app.dependencies.db import SessionDep
from app.schemas.base import (
    SpeciesCreate,
)
from app.schemas.morphology import (
    SpeciesRead,
)

router = APIRouter(
    prefix="/species",
    tags=["species"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    db_species = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species
