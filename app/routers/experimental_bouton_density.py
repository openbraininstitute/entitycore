
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.base import BrainLocation
from app.models.density import ExperimentalBoutonDensity
from app.schemas.density import (
    ExperimentalBoutonDensityCreate,
    ExperimentalBoutonDensityRead,
)

router = APIRouter(
    prefix="/experimental_bouton_density",
    tags=["experimental_bouton_density"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{experimental_bouton_density_id}",
    response_model=ExperimentalBoutonDensityRead,
)
async def read_experimental_bouton_density(
    experimental_bouton_density_id: int, db: Session = Depends(get_db)
):
    experimental_bouton_density = (
        db.query(ExperimentalBoutonDensity)
        .filter(ExperimentalBoutonDensity.id == experimental_bouton_density_id)
        .first()
    )

    if experimental_bouton_density is None:
        raise HTTPException(status_code=404, detail="experimental_bouton_density not found")
    ret = ExperimentalBoutonDensityRead.model_validate(experimental_bouton_density)
    return ret


@router.post("/", response_model=ExperimentalBoutonDensityRead)
def create_experimental_bouton_density(
    density: ExperimentalBoutonDensityCreate, db: Session = Depends(get_db)
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_bouton_density = ExperimentalBoutonDensity(**dump)
    db.add(db_experimental_bouton_density)
    db.commit()
    db.refresh(db_experimental_bouton_density)
    return db_experimental_bouton_density


@router.get("/", response_model=list[ExperimentalBoutonDensityRead])
async def read_experimental_bouton_density(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(ExperimentalBoutonDensity).offset(skip).limit(limit).all()
    return users
