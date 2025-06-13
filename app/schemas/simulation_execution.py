from app.db.types import SimulationExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead


class SimulationExecutionCreate(ActivityCreate):
    status: SimulationExecutionStatus


class SimulationExecutionRead(ActivityRead):
    status: SimulationExecutionStatus
