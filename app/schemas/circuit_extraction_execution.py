from app.db.types import CircuitExtractionExecutionStatus
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class CircuitExtractionExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    status: CircuitExtractionExecutionStatus


class CircuitExtractionExecutionRead(ActivityRead, ExecutionActivityMixin):
    status: CircuitExtractionExecutionStatus


class CircuitExtractionExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    status: CircuitExtractionExecutionStatus | None = None


CircuitExtractionExecutionAdminUpdate = make_update_schema(
    CircuitExtractionExecutionCreate,
    "CircuitExtractionExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
