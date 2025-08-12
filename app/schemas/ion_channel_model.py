from pydantic import BaseModel, ConfigDict, Field

from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)


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


class IonChannelModelCreate(
    IonChannelModelBase,
    ScientificArtifactCreate,
):
    pass


class IonChannelModelRead(
    IonChannelModelBase,
    ScientificArtifactRead,
):
    pass
