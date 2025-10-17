from app.db.types import CircuitExtractionExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class CircuitExtractionExecutionCreate(ActivityCreate):
    status: CircuitExtractionExecutionStatus


class CircuitExtractionExecutionRead(ActivityRead):
    status: CircuitExtractionExecutionStatus


class CircuitExtractionExecutionUserUpdate(ActivityUpdate):
    status: CircuitExtractionExecutionStatus | None = None


CircuitExtractionExecutionAdminUpdate = make_update_schema(
    CircuitExtractionExecutionCreate,
    "CircuitExtractionExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
