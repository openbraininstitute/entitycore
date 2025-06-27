from app.db.types import SimulationExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate


class SimulationExecutionCreate(ActivityCreate):
    status: SimulationExecutionStatus


class SimulationExecutionRead(ActivityRead):
    pass


class SimulationExecutionUpdate(ActivityUpdate):
    pass
