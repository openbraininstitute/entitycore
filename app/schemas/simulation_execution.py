from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class SimulationExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    pass


class SimulationExecutionRead(ActivityRead, ExecutionActivityMixin):
    pass


class SimulationExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    pass


SimulationExecutionAdminUpdate = make_update_schema(
    SimulationExecutionCreate,
    "SimulationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
