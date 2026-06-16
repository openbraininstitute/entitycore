import uuid

from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionReadMixin
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.me_model import NestedMEModel
from app.schemas.utils import make_update_schema


class SingleNeuronSynaptomeBaseMixin(NameDescriptionMixin):
    seed: int


class SingleNeuronSynaptomeCreate(
    SingleNeuronSynaptomeBaseMixin,
    EntityCreate,
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


class NestedSynaptome(SingleNeuronSynaptomeBaseMixin, NestedEntityRead):
    pass


class SingleNeuronSynaptomeRead(
    SingleNeuronSynaptomeBaseMixin,
    EntityRead,
    BrainRegionReadMixin,
):
    me_model: NestedMEModel
