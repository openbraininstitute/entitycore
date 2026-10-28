import uuid

from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.simulation import NestedSimulationRead
from app.schemas.utils import make_update_schema


class SimulationCampaignBaseMixin(NameDescriptionMixin):
    scan_parameters: JSON_DICT
    entity_id: uuid.UUID


class SimulationCampaignCreate(SimulationCampaignBaseMixin, EntityCreate):
    pass


SimulationCampaignUserUpdate = make_update_schema(
    SimulationCampaignCreate, "SimulationCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
SimulationCampaignAdminUpdate = make_update_schema(
    SimulationCampaignCreate,
    "SimulationCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSimulationCampaignRead(SimulationCampaignBaseMixin, NestedEntityRead):
    pass


class SimulationCampaignRead(
    SimulationCampaignBaseMixin,
    EntityRead,
):
    simulations: list[NestedSimulationRead]
