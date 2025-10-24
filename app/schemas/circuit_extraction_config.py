import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.utils import make_update_schema


class CircuitExtractionConfigBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    circuit_id: uuid.UUID
    scan_parameters: JSON_DICT


class CircuitExtractionConfigCreate(CircuitExtractionConfigBase, AuthorizationOptionalPublicMixin):
    pass


CircuitExtractionConfigUserUpdate = make_update_schema(
    CircuitExtractionConfigCreate, "CircuitExtractionConfigUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

CircuitExtractionConfigAdminUpdate = make_update_schema(
    CircuitExtractionConfigCreate,
    "CircuitExtractionConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedCircuitExtractionConfigRead(
    CircuitExtractionConfigBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class CircuitExtractionConfigRead(
    NestedCircuitExtractionConfigRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    pass
