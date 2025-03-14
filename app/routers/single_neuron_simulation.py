import sqlalchemy as sa
from fastapi import APIRouter
from sqlalchemy.orm import joinedload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import SingleNeuronSimulation
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.simulation import (
    SingleNeuronSimulationCreate,
    SingleNeuronSimulationRead,
)

router = APIRouter(
    prefix="/single-neuron-simulation",
    tags=["single-neuron-simulation"],
)


@router.get(
    "/{id_}",
    response_model=SingleNeuronSimulationRead,
)
def read_single_neuron_simulation(
    db: SessionDep,
    id_: int,
    project_context: VerifiedProjectContextHeader,
):
    with ensure_result(error_message="SingleNeuronSimulation not found"):
        query = (
            constrain_to_accessible_entities(
                sa.select(SingleNeuronSimulation),
                project_context.project_id,
            )
            .filter(SingleNeuronSimulation.id == id_)
            .options(joinedload(SingleNeuronSimulation.me_model))
        )

        row = db.execute(query).unique().scalar_one()

    return SingleNeuronSimulationRead.model_validate(row)


@router.post("", response_model=SingleNeuronSimulationRead)
def create_single_neuron_simulation(
    project_context: VerifiedProjectContextHeader,
    json_model: SingleNeuronSimulationCreate,
    db: SessionDep,
):
    kwargs = json_model.model_dump() | {"authorized_project_id": project_context.project_id}

    db_model = SingleNeuronSimulation(**kwargs)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    return db_model
