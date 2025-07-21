from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
)
from app.schemas.subject import SubjectReadMixin


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
    channelpedia_link: str | None = None


class IonChannelModelCreate(IonChannelModelBase, ScientificArtifactCreate):
    pass


class IonChannelModelRead(
    IonChannelModelBase,
    CreationMixin,
    IdentifiableMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    LicensedReadMixin,
    SubjectReadMixin,
    BrainRegionReadMixin,
):
    pass


class IonChannelModelWAssets(IonChannelModelRead, AssetsMixin):
    pass


class IonChannelModelExpanded(
    IonChannelModelWAssets, CreatedByUpdatedByMixin, ContributionReadWithoutEntityMixin
):
    pass
