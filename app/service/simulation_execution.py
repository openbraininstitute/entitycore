import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

from app.db.model import (
    SimulationExecution,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.db import SessionDep
from app.queries.common import router_create_one, router_read_one
from app.schemas.simulation_execution import (
    SimulationExecutionCreate,
    SimulationExecutionRead,
)


def _load(query: sa.Select):
    return query.options(
        joinedload(SimulationExecution.created_by),
        joinedload(SimulationExecution.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationExecutionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationExecution,
        authorized_project_id=user_context.project_id,
        response_schema_class=SimulationExecutionRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulationExecutionCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulationExecutionRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulationExecution,
        response_schema_class=SimulationExecutionRead,
        apply_operations=_load,
    )
