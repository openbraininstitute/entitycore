from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class CircuitExtractionExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    pass


class CircuitExtractionExecutionRead(ActivityRead, ExecutionActivityMixin):
    pass


class CircuitExtractionExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    pass


CircuitExtractionExecutionAdminUpdate = make_update_schema(
    CircuitExtractionExecutionCreate,
    "CircuitExtractionExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
