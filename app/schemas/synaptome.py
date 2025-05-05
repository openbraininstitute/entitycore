import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.me_model import NestedMEModel as MEModelRead


class SingleNeuronSynaptomeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    seed: int


class SingleNeuronSynaptomeCreate(
    SingleNeuronSynaptomeBase,
    AuthorizationOptionalPublicMixin,
):
    me_model_id: uuid.UUID
    brain_region_id: uuid.UUID


class SingleNeuronSynaptomeRead(
    SingleNeuronSynaptomeBase,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
):
    me_model: MEModelRead
    brain_region: BrainRegionRead
