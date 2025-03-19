import uuid
from pydantic import ConfigDict, BaseModel

from app.schemas.base import (
    BrainRegionRead,
    CreationMixin,
    AuthorizationOptionalPublicMixin,
    AuthorizationMixin,
    SpeciesRead,
    StrainRead,
)

from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.emodel import ExemplarMorphology as MModel, EModelBase


class MEModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    status: str
    validated: bool = False


class MEModelCreate(MEModelBase, AuthorizationOptionalPublicMixin):
    name: str
    description: str
    status: str
    validated: bool = False
    brain_region_id: int
    mmodel_id: uuid.UUID
    emodel_id: uuid.UUID
    species_id: uuid.UUID
    strain_id: uuid.UUID


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
    mmodel: MModel
    emodel: EModelBase
