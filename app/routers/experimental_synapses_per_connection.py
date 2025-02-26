from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import BrainLocation, ExperimentalSynapsesPerConnection
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)

router = APIRouter(
    prefix="/experimental-synapses-per-connection",
    tags=["experimental_synapses_per_connection"],
)


@router.get("/", response_model=list[ExperimentalSynapsesPerConnectionRead])
def get(
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    return (
        constrain_to_accessible_entities(
            db.query(ExperimentalSynapsesPerConnection), project_context.project_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id_}", response_model=ExperimentalSynapsesPerConnectionRead)
def read_experimental_synapses_per_connection(
    project_context: VerifiedProjectContextHeader,
    id_: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalSynapsesPerConnection not found"):
        row = (
            constrain_to_accessible_entities(
                db.query(ExperimentalSynapsesPerConnection),
                project_context.project_id,
            )
            .filter(ExperimentalSynapsesPerConnection.id == id_)
            .one()
        )

    return ExperimentalSynapsesPerConnectionRead.model_validate(row)


@router.post("/", response_model=ExperimentalSynapsesPerConnectionRead)
def create_experimental_synapses_per_connection(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalSynapsesPerConnectionCreate,
    db: SessionDep,
):
    dump = density.model_dump()
    if density.brain_location:
        dump["brain_location"] = BrainLocation(**density.brain_location.model_dump())

    row = ExperimentalSynapsesPerConnection(
        **dump, authorized_project_id=project_context.project_id
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
