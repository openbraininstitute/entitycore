import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import SingleNeuronSimulationStatus
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.me_model import MEModelBase


class MEModelRead(MEModelBase):
    id: uuid.UUID


class SingleNeuronSimulationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    seed: int
    status: SingleNeuronSimulationStatus
    injectionLocation: list[str]
    recordingLocation: list[str]


class SingleNeuronSimulationCreate(
    SingleNeuronSimulationBase,
    AuthorizationOptionalPublicMixin,
):
    me_model_id: uuid.UUID
    brain_region_id: int


class SingleNeuronSimulationRead(
    SingleNeuronSimulationBase,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
):
    me_model: MEModelRead
    brain_region: BrainRegionRead
