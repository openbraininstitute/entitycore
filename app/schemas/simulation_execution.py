from app.db.types import SimulationExecutionStatus
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class SimulationExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    status: SimulationExecutionStatus


class SimulationExecutionRead(ActivityRead, ExecutionActivityMixin):
    status: SimulationExecutionStatus


class SimulationExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    status: SimulationExecutionStatus | None = None


SimulationExecutionAdminUpdate = make_update_schema(
    SimulationExecutionCreate,
    "SimulationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
