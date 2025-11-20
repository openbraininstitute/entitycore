from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetsMixin
from app.schemas.base import BrainRegionReadMixin, CreationMixin
from app.schemas.scientific_artifact import (
    NestedScientificArtifactRead,
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.subject import SubjectReadMixin
from app.schemas.utils import make_update_schema


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
    temperature_celsius: int | None
    is_stochastic: bool = False
    neuron_block: NeuronBlock


class IonChannelModelCreate(
    IonChannelModelBase,
    ScientificArtifactCreate,
):
    pass


IonChannelModelUserUpdate = make_update_schema(IonChannelModelCreate, "IonChannelModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
IonChannelModelAdminUpdate = make_update_schema(
    IonChannelModelCreate,
    "IonChannelModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class IonChannelModelRead(
    IonChannelModelBase,
    NestedScientificArtifactRead,
    SubjectReadMixin,
    BrainRegionReadMixin,
    CreationMixin,
):
    pass


class IonChannelModelWAssets(
    IonChannelModelRead,
    AssetsMixin,
):
    pass


class IonChannelModelExpanded(
    IonChannelModelBase,
    ScientificArtifactRead,
):
    pass
