from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    BrainLocation,
    ExperimentalBoutonDensity,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.density import (
    ExperimentalBoutonDensityCreate,
    ExperimentalBoutonDensityRead,
)

router = APIRouter(
    prefix="/experimental-bouton-density",
    tags=["experimental-bouton-density"],
)


@router.get("/", response_model=list[ExperimentalBoutonDensityRead])
def read_experimental_bouton_densities(
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    return (
        constrain_to_accessible_entities(
            db.query(ExperimentalBoutonDensity), project_context.project_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id_}", response_model=ExperimentalBoutonDensityRead)
def read_experimental_bouton_density(
    project_context: VerifiedProjectContextHeader,
    id_: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalBoutonDensity not found"):
        row = (
            constrain_to_accessible_entities(
                db.query(ExperimentalBoutonDensity), project_context.project_id
            )
            .filter(ExperimentalBoutonDensity.id == id_)
            .one()
        )

    return ExperimentalBoutonDensityRead.model_validate(row)


@router.post("/", response_model=ExperimentalBoutonDensityRead)
def create_experimental_bouton_density(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalBoutonDensityCreate,
    db: SessionDep,
):
    dump = density.model_dump()

    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    row = ExperimentalBoutonDensity(**dump, authorized_project_id=project_context.project_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
