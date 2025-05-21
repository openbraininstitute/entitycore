import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.ion_channel_model import IonChannelModelWAssets
from app.schemas.morphology import ReconstructionMorphologyBase


class ExemplarMorphology(CreationMixin, ReconstructionMorphologyBase, IdentifiableMixin):
    pass


class EModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    name: str
    iteration: str
    score: float
    seed: int


class EModelCreate(EModelBase, AuthorizationOptionalPublicMixin):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    exemplar_morphology_id: uuid.UUID


class EModelRead(
    EModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
):
    id: uuid.UUID
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology
    ion_channel_models: list[IonChannelModelWAssets]
