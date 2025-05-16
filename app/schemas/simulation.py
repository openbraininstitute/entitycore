import uuid

from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    SingleNeuronSimulationBase,
)
from app.schemas.me_model import NestedMEModel
from app.schemas.synaptome import NestedSynaptome


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
):
    me_model: NestedMEModel


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
):
    synaptome: NestedSynaptome
