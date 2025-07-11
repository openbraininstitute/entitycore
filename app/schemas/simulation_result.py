import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)


class SimulationResultBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    simulation_id: uuid.UUID


class SimulationResultCreate(SimulationResultBase, AuthorizationOptionalPublicMixin):
    pass


class NestedSimulationResultRead(SimulationResultBase, EntityTypeMixin, IdentifiableMixin):
    pass


class SimulationResultRead(
    NestedSimulationResultRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
