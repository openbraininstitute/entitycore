from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class CircuitExtractionConfigGenerationCreate(ActivityCreate):
    pass


class CircuitExtractionConfigGenerationRead(ActivityRead):
    pass


class CircuitExtractionConfigGenerationUserUpdate(ActivityUpdate):
    pass


CircuitExtractionConfigGenerationAdminUpdate = make_update_schema(
    CircuitExtractionConfigGenerationCreate,
    "CircuitExtractionConfigGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
