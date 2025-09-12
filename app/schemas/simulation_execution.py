from app.db.types import SimulationExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class SimulationExecutionCreate(ActivityCreate):
    status: SimulationExecutionStatus


class SimulationExecutionRead(ActivityRead):
    status: SimulationExecutionStatus


class SimulationExecutionUpdate(ActivityUpdate):
    status: SimulationExecutionStatus | None = None


SimulationExecutionAdminUpdate = make_update_schema(
    SimulationExecutionCreate,
    "SimulationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
