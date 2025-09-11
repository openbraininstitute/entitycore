import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT, SingleNeuronSimulationStatus
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.me_model import NestedMEModel
from app.schemas.synaptome import NestedSynaptome
from app.schemas.utils import make_update_schema


class SingleNeuronSimulationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    seed: int
    status: SingleNeuronSimulationStatus
    injection_location: list[str]
    recording_location: list[str]


class SingleNeuronSimulationCreate(
    SingleNeuronSimulationBase,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
):
    me_model_id: uuid.UUID


SingleNeuronSimulationUpdate = make_update_schema(
    SingleNeuronSimulationCreate, "SingleNeuronSimulationUpdate"
)  # pyright: ignore [reportInvalidTypeForm]


class SingleNeuronSimulationRead(
    SingleNeuronSimulationBase,
    BrainRegionReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
):
    me_model: NestedMEModel


class SingleNeuronSynaptomeSimulationCreate(
    SingleNeuronSimulationBase,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
):
    synaptome_id: uuid.UUID


SingleNeuronSynaptomeSimulationUpdate = make_update_schema(
    SingleNeuronSynaptomeSimulationCreate, "SingleNeuronSynaptomeSimulationUpdate"
)  # pyright: ignore [reportInvalidTypeForm]


class SingleNeuronSynaptomeSimulationRead(
    SingleNeuronSimulationBase,
    BrainRegionReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
):
    synaptome: NestedSynaptome


class SimulationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    simulation_campaign_id: uuid.UUID
    entity_id: uuid.UUID
    scan_parameters: JSON_DICT


class SimulationCreate(SimulationBase, AuthorizationOptionalPublicMixin):
    pass


SimulationUpdate = make_update_schema(SimulationCreate, "SimulationUpdate")  # pyright: ignore [reportInvalidTypeForm]


class NestedSimulationRead(SimulationBase, EntityTypeMixin, IdentifiableMixin):
    pass


class SimulationRead(
    NestedSimulationRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
