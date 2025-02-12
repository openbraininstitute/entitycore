from fastapi import APIRouter, HTTPException

from app.db.model import (
    BrainLocation,
    ExperimentalBoutonDensity,
)
from app.dependencies.db import SessionDep
from app.schemas.density import (
    ExperimentalBoutonDensityCreate,
    ExperimentalBoutonDensityRead,
)

router = APIRouter(
    prefix="/experimental_bouton_density",
    tags=["experimental_bouton_density"],
)


@router.get("/", response_model=list[ExperimentalBoutonDensityRead])
def read_experimental_bouton_densities(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(ExperimentalBoutonDensity).offset(skip).limit(limit).all()


@router.get(
    "/{experimental_bouton_density_id}",
    response_model=ExperimentalBoutonDensityRead,
)
def read_experimental_bouton_density(experimental_bouton_density_id: int, db: SessionDep):
    experimental_bouton_density = (
        db.query(ExperimentalBoutonDensity)
        .filter(ExperimentalBoutonDensity.id == experimental_bouton_density_id)
        .first()
    )

    if experimental_bouton_density is None:
        raise HTTPException(status_code=404, detail="experimental_bouton_density not found")
    return ExperimentalBoutonDensityRead.model_validate(experimental_bouton_density)


@router.post("/", response_model=ExperimentalBoutonDensityRead)
def create_experimental_bouton_density(density: ExperimentalBoutonDensityCreate, db: SessionDep):
    dump = density.model_dump()

    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    db_experimental_bouton_density = ExperimentalBoutonDensity(**dump)
    db.add(db_experimental_bouton_density)
    db.commit()
    db.refresh(db_experimental_bouton_density)
    return db_experimental_bouton_density
