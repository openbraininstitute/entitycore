
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

    description: str
    name: str
    iteration: str
    score: int
    seed: int
