import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import AgentRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.me_model import NestedMEModel


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
    brain_region_id: int


class NestedSynaptome(SingleNeuronSynaptomeBase, CreationMixin, IdentifiableMixin):
    pass


class SingleNeuronSynaptomeRead(
    SingleNeuronSynaptomeBase,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
    ContributionReadWithoutEntityMixin,
):
    me_model: NestedMEModel
    brain_region: BrainRegionRead
    createdBy: AgentRead | None
    updatedBy: AgentRead | None
