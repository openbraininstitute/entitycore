from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.model import Strain
from app.dependencies.db import get_db
from app.schemas.base import (
    StrainCreate,
)
from app.schemas.morphology import (
    StrainRead,
)

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: Session = Depends(get_db)):
    db_strain = Strain(
        name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id
    )
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain
