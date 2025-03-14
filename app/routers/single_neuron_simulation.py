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
    db_model = SingleNeuronSimulation(
        name=json_model.name,
        description=json_model.description,
        seed=json_model.seed,
        status=json_model.status,
        injectionLocation=json_model.injectionLocation,
        recordingLocation=json_model.recordingLocation,
        me_model_id=json_model.me_model_id,
        brain_region_id=json_model.brain_region_id,
        authorized_project_id=project_context.project_id,
        authorized_public=json_model.authorized_public,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    return db_model
