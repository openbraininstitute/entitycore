from fastapi import APIRouter

from app.db.model import Species
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import (
    SpeciesCreate,
)
from app.schemas.morphology import (
    SpeciesRead,
)

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get("/", response_model=list[SpeciesRead])
def get(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Species).offset(skip).limit(limit).all()


@router.get("/{role_id}", response_model=SpeciesRead)
def read_species(role_id: int, db: SessionDep):
    with ensure_result(error_message="Species not found"):
        row = db.query(Species).filter(Species.id == role_id).one()
    return row


@router.post("/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    db_species = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species
