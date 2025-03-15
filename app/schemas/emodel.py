from pydantic import BaseModel, ConfigDict

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
from app.schemas.morphology import ReconstructionMorphologyBase


class ExemplarMorphology(CreationMixin, ReconstructionMorphologyBase):
    pass


class EModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    name: str
    iteration: str
    score: float
    seed: int


class EModelCreate(EModelBase, AuthorizationOptionalPublicMixin):
    species_id: int
    strain_id: int | None
    brain_region_id: int
    exemplar_morphology_id: int
    legacy_id: str | None


class EModelRead(
    EModelBase,
    CreationMixin,
    AuthorizationMixin,
):
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology
