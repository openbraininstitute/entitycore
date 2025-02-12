from fastapi import APIRouter

from app.db.model import Strain
from app.dependencies.db import SessionDep
from app.schemas.base import (
    StrainCreate,
)
from app.schemas.morphology import (
    StrainRead,
)

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)


@router.post("/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: SessionDep):
    db_strain = Strain(
        name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id
    )
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain
