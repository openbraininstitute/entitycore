from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import Species
from app.dependencies.db import get_db
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
def create_species(species: SpeciesCreate, db: Session = Depends(get_db)):
    db_species = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species
