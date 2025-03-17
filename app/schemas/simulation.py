from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
)
from app.schemas.me_model import MEModelRead


class SingleNeuronSimulationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    seed: int
    status: str
    injectionLocation: list[str]
    recordingLocation: list[str]


class SingleNeuronSimulationCreate(
    SingleNeuronSimulationBase,
    AuthorizationOptionalPublicMixin,
):
    me_model_id: int
    brain_region_id: int


class SingleNeuronSimulationRead(
    SingleNeuronSimulationBase,
    AuthorizationMixin,
    CreationMixin,
):
    me_model: MEModelRead
    brain_region: BrainRegionRead
