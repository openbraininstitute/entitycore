import uuid

from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionCreateMixin, BrainRegionReadMixin
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.me_model import NestedMEModel
from app.schemas.synaptome import NestedSynaptome
from app.schemas.utils import make_update_schema


class SingleNeuronSimulationBaseMixin(NameDescriptionMixin):
    seed: int
    injection_location: list[str]
    recording_location: list[str]


class SingleNeuronSimulationCreate(
    SingleNeuronSimulationBaseMixin,
    BrainRegionCreateMixin,
    EntityCreate,
):
    me_model_id: uuid.UUID


SingleNeuronSimulationUserUpdate = make_update_schema(
    SingleNeuronSimulationCreate, "SingleNeuronSimulationUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

SingleNeuronSimulationAdminUpdate = make_update_schema(
    SingleNeuronSimulationCreate,
    "SingleNeuronSimulationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class SingleNeuronSimulationRead(
    SingleNeuronSimulationBaseMixin,
    BrainRegionReadMixin,
    EntityRead,
):
    me_model: NestedMEModel


class SingleNeuronSynaptomeSimulationCreate(
    SingleNeuronSimulationBaseMixin,
    BrainRegionCreateMixin,
    EntityCreate,
):
    synaptome_id: uuid.UUID


SingleNeuronSynaptomeSimulationUserUpdate = make_update_schema(
    SingleNeuronSynaptomeSimulationCreate, "SingleNeuronSynaptomeSimulationUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

SingleNeuronSynaptomeSimulationAdminUpdate = make_update_schema(
    SingleNeuronSynaptomeSimulationCreate,
    "SingleNeuronSynaptomeSimulationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class SingleNeuronSynaptomeSimulationRead(
    SingleNeuronSimulationBaseMixin,
    BrainRegionReadMixin,
    EntityRead,
):
    synaptome: NestedSynaptome


class SimulationBaseMixin(NameDescriptionMixin):
    simulation_campaign_id: uuid.UUID
    entity_id: uuid.UUID
    scan_parameters: JSON_DICT
    number_neurons: int


class SimulationCreate(SimulationBaseMixin, EntityCreate):
    pass


SimulationUserUpdate = make_update_schema(SimulationCreate, "SimulationUserUpdate")  # pyright: ignore [reportInvalidTypeForm]

SimulationAdminUpdate = make_update_schema(
    SimulationCreate,
    "SimulationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSimulationRead(SimulationBaseMixin, NestedEntityRead):
    pass


class SimulationRead(
    SimulationBaseMixin,
    EntityRead,
):
    pass
