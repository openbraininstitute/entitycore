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
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.me_model import NestedMEModel
from app.schemas.utils import make_update_schema


class SingleNeuronSynaptomeBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    seed: int


class SingleNeuronSynaptomeCreate(
    SingleNeuronSynaptomeBase,
    AuthorizationOptionalPublicMixin,
):
    me_model_id: uuid.UUID
    brain_region_id: uuid.UUID


SingleNeuronSynaptomeUserUpdate = make_update_schema(
    SingleNeuronSynaptomeCreate, "SingleNeuronSynaptomeUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

SingleNeuronSynaptomeAdminUpdate = make_update_schema(
    SingleNeuronSynaptomeCreate,
    "SingleNeuronSynaptomeAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


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
