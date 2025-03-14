from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    BrainRegionRead,
    CreationMixin,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.etype import ETypeClassRead
from app.schemas.mtype import MTypeClassRead


class ExemplarMorphology(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class EModelRead(
    BaseModel,
    CreationMixin,
    AuthorizationMixin,
):
    model_config = ConfigDict(from_attributes=True)
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology

    description: str
    name: str
    iteration: str
    score: int
    seed: int
