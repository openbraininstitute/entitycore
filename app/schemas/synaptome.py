import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.me_model import NestedMEModel
from app.schemas.utils import make_update_schema


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


SingleNeuronSynaptomeUpdate = make_update_schema(
    SingleNeuronSynaptomeCreate, "SingleNeuronSynaptomeUpdate"
)


class NestedSynaptome(SingleNeuronSynaptomeBase, CreationMixin, IdentifiableMixin):
    pass


class SingleNeuronSynaptomeRead(
    SingleNeuronSynaptomeBase,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
    ContributionReadWithoutEntityMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
):
    me_model: NestedMEModel
    brain_region: BrainRegionRead
