import uuid

from pydantic import BaseModel, ConfigDict

from app.db.model import ValidationStatus
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
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
from app.schemas.emodel import EModelRead
from app.schemas.morphology import ReconstructionMorphologyRead


class MEModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    validation_status: ValidationStatus = ValidationStatus.created
    holding_current: int
    threshold_current: int


# To be used by entities who reference MEModel
class NestedMEModel(MEModelBase, CreationMixin, IdentifiableMixin):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None


class MEModelCreate(MEModelBase, AuthorizationOptionalPublicMixin):
    brain_region_id: uuid.UUID
    morphology_id: uuid.UUID
    emodel_id: uuid.UUID
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


class MEModelRead(
    MEModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
):
    id: uuid.UUID
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    morphology: ReconstructionMorphologyRead
    emodel: EModelRead
