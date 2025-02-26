from fastapi import APIRouter

from app.db.model import Species
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import SpeciesCreate, SpeciesRead

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get("/", response_model=list[SpeciesRead])
def get(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Species).offset(skip).limit(limit).all()


@router.get("/{id_}", response_model=SpeciesRead)
def read_species(id_: int, db: SessionDep):
    with ensure_result(error_message="Species not found"):
        row = db.query(Species).filter(Species.id == id_).one()
    return SpeciesRead.model_validate(row)


@router.post("/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: SessionDep):
    row = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
