from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class CircuitExtractionCampaignBaseMixin(NameDescriptionMixin):
    scan_parameters: JSON_DICT


class CircuitExtractionCampaignCreate(
    CircuitExtractionCampaignBaseMixin,
    EntityCreate,
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
    CircuitExtractionCampaignBaseMixin,
    NestedEntityRead,
):
    pass


class CircuitExtractionCampaignRead(
    CircuitExtractionCampaignBaseMixin,
    EntityRead,
):
    pass
