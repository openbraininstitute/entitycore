import uuid

from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class CircuitExtractionConfigBaseMixin(NameDescriptionMixin):
    circuit_id: uuid.UUID
    scan_parameters: JSON_DICT


class CircuitExtractionConfigCreate(CircuitExtractionConfigBaseMixin, EntityCreate):
    pass


CircuitExtractionConfigUserUpdate = make_update_schema(
    CircuitExtractionConfigCreate, "CircuitExtractionConfigUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

CircuitExtractionConfigAdminUpdate = make_update_schema(
    CircuitExtractionConfigCreate,
    "CircuitExtractionConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedCircuitExtractionConfigRead(CircuitExtractionConfigBaseMixin, NestedEntityRead):
    pass


class CircuitExtractionConfigRead(
    CircuitExtractionConfigBaseMixin,
    EntityRead,
):
    pass
