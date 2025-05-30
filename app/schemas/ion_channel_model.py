from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.species import NestedSpeciesRead


class UseIon(BaseModel):
    ion_name: str
    read: list[str] = []
    write: list[str] = []
    valence: int | None = None
    main_ion: bool | None = None


class NeuronBlock(BaseModel):
    global_: list[dict[str, str | None]] = Field(default=[], alias="global")
    range: list[dict[str, str | None]] = []
    useion: list[UseIon] = []
    nonspecific: list[dict[str, str | None]] = []


class IonChannelModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    name: str
    nmodl_suffix: str
    is_ljp_corrected: bool = False
    is_temperature_dependent: bool = False
    temperature_celsius: int
    is_stochastic: bool = False
    neuron_block: NeuronBlock


class IonChannelModelCreate(IonChannelModelBase, AuthorizationOptionalPublicMixin):
    species_id: UUID
    strain_id: UUID | None = None
    brain_region_id: UUID


class IonChannelModelRead(
    IonChannelModelBase, CreationMixin, IdentifiableMixin, AuthorizationMixin, EntityTypeMixin
):
    species: NestedSpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead


class IonChannelModelWAssets(IonChannelModelRead, AssetsMixin):
    pass


class IonChannelModelExpanded(IonChannelModelWAssets):
    contributions: list[ContributionReadWithoutEntity]
