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
from app.schemas.utils import make_update_schema


class CircuitExtractionCampaignBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT


class CircuitExtractionCampaignCreate(
    CircuitExtractionCampaignBase, AuthorizationOptionalPublicMixin
):
    pass


CircuitExtractionCampaignUserUpdate = make_update_schema(
    CircuitExtractionCampaignCreate, "CircuitExtractionCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
CircuitExtractionCampaignAdminUpdate = make_update_schema(
    CircuitExtractionCampaignCreate,
    "CircuitExtractionCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedCircuitExtractionCampaignRead(
    CircuitExtractionCampaignBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class CircuitExtractionCampaignRead(
    NestedCircuitExtractionCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
