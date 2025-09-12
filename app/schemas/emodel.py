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
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.ion_channel_model import IonChannelModelWAssets
from app.schemas.morphology import ReconstructionMorphologyBase
from app.schemas.species import NestedSpeciesRead, NestedStrainRead
from app.schemas.utils import make_update_schema


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


EModelUpdate = make_update_schema(EModelCreate, "EModelUpdate")  # pyright: ignore [reportInvalidTypeForm]
EModelAdminUpdate = make_update_schema(
    EModelCreate,
    "EModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class EModelRead(
    EModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
):
    id: uuid.UUID
    species: NestedSpeciesRead
    strain: NestedStrainRead | None
    brain_region: BrainRegionRead
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology


class EModelReadExpanded(EModelRead, AssetsMixin):
    ion_channel_models: list[IonChannelModelWAssets]
