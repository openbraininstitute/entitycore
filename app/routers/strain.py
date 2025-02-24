from fastapi import APIRouter

from app.db.model import Strain
from app.dependencies.db import SessionDep
from app.errors import ensure_result
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


@router.get("/", response_model=list[StrainRead])
def read_organizations(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Strain).offset(skip).limit(limit).all()


@router.get("/{organization_id}", response_model=StrainRead)
def read_organization(organization_id: int, db: SessionDep):
    with ensure_result(error_message="Strain not found"):
        row = db.query(Strain).filter(Strain.id == organization_id).one()
    return StrainRead.model_validate(row)


@router.post("/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: SessionDep):
    db_strain = Strain(
        name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id
    )
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain
