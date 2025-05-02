import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.db.types import EntityType, SingleNeuronSimulationStatus
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
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
    injectionLocation: list[str]
    recordingLocation: list[str]


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
):
    me_model: NestedMEModel
    type: Literal[EntityType.single_neuron_simulation] = EntityType.single_neuron_simulation


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
):
    synaptome: NestedSynaptome
    type: Literal[EntityType.single_neuron_synaptome_simulation] = (
        EntityType.single_neuron_synaptome_simulation
    )
