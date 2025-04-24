from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
    SpeciesRead,
    StrainRead,
)


class NmodlParameters(BaseModel):
    range: list[str]
    read: list[str] | None = None
    suffix: str | None = None
    useion: list[str] | None = None
    write: list[str] | None = None
    nonspecific: list[str] | None = None
    valence: int | None = None


class Ion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class IonChannelModel(CreationMixin, IdentifiableMixin, AuthorizationMixin, AssetsMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    is_ljp_corrected: bool
    is_temperature_dependent: bool
    temperature_celsius: int
    stochastic: bool

    nmodl_parameters: NmodlParameters

    ions: list[Ion]
