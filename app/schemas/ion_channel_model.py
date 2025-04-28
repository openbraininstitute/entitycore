from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
    SpeciesRead,
    StrainRead,
)


class UseIon(BaseModel):
    ion_name: str
    ontology_id: str | None
    read: list[str]
    write: list[str]
    valence: int | None = None
    main_ion: bool | None = None


class NeuronBlock(BaseModel):
    global_: list[str] = Field(alias="global")
    range: list[str]
    useion: list[UseIon]
    nonspecific: list[str]


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
    acronym: str | None = None
