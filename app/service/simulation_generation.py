import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

from app.db.model import (
    SimulationGeneration,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.db import SessionDep
from app.queries.common import router_create_one, router_read_one
from app.schemas.simulation_generation import (
    SimulationGenerationCreate,
    SimulationGenerationRead,
)


def _load(query: sa.Select):
    return query.options(
        joinedload(SimulationGeneration.created_by),
        joinedload(SimulationGeneration.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationGenerationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationGeneration,
        authorized_project_id=user_context.project_id,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulationGenerationCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulationGenerationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulationGeneration,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )
