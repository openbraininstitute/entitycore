import uuid

from pydantic import BaseModel, ConfigDict

from app.db.model import ValidationStatus
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.emodel import EModelBase, ExemplarMorphology as Morphology


class EModel(EModelBase, CreationMixin):
    id: uuid.UUID


class MEModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    validation_status: ValidationStatus = ValidationStatus.created


class MEModelCreate(MEModelBase, AuthorizationOptionalPublicMixin):
    brain_region_id: int
    morphology_id: uuid.UUID
    emodel_id: uuid.UUID
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


class MEModelRead(
    MEModelBase,
    CreationMixin,
    AuthorizationMixin,
):
    id: uuid.UUID
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    morphology: Morphology
    emodel: EModel
