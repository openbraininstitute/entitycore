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


class SimulationCampaignBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT


class SimulationCampaignCreate(SimulationCampaignBase, AuthorizationOptionalPublicMixin):
    pass


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
