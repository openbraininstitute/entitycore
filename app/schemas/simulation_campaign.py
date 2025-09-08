import uuid
from typing import Annotated

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
from app.schemas.simulation import NestedSimulationRead
from app.schemas.utils import make_update_schema


class SimulationCampaignBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT
    entity_id: uuid.UUID


class SimulationCampaignCreate(SimulationCampaignBase, AuthorizationOptionalPublicMixin):
    pass


SimulationCampaignUpdate = Annotated[
    BaseModel, make_update_schema(SimulationCampaignCreate, "SimulationCampaignUpdate")
]


class NestedSimulationCampaignRead(SimulationCampaignBase, EntityTypeMixin, IdentifiableMixin):
    pass


class SimulationCampaignRead(
    NestedSimulationCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    simulations: list[NestedSimulationRead]
