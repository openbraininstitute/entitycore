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


class Ion(CreationMixin, IdentifiableMixin, AuthorizationMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ontology_id: str | None = None
    name: str


class UseIon(BaseModel):
    ion: Ion
    read: list[str] | None = None
    write: list[str] | None = None
    valence: int | None = None
    main_ion: bool | None = None


class NeuronBlock(BaseModel):
    global_: list[str] | None = None
    range: list[str] | None = None
    suffix: str | None = None
    useion: list[UseIon] | None = None
    nonspecific: list[str] | None = None


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
    is_stochastic: bool
    neuron_block: NeuronBlock
