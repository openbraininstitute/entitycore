import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT, SingleNeuronSimulationStatus
from app.schemas.activity import NestedActivityRead
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
    used_by: list[NestedActivityRead]


class SingleNeuronSynaptomeSimulationCreate(
    SingleNeuronSimulationBase,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
):
    synaptome_id: uuid.UUID


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
    used_by: list[NestedActivityRead]


class SimulationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    simulation_campaign_id: uuid.UUID
    entity_id: uuid.UUID
    scan_parameters: JSON_DICT


class SimulationCreate(SimulationBase, AuthorizationOptionalPublicMixin):
    pass


class UsageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    usage_activity_id: uuid.UUID
    usage_entity_id: uuid.UUID


class NestedSimulationRead(SimulationBase, EntityTypeMixin, IdentifiableMixin):
    used_by: list[NestedActivityRead]


class SimulationRead(
    NestedSimulationRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
