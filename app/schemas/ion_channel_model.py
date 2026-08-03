from pydantic import Field

from app.schemas.asset import AssetsMixin
from app.schemas.base import NameDescriptionMixin, Schema
from app.schemas.brain_region import BrainRegionReadMixin
from app.schemas.scientific_artifact import (
    NestedScientificArtifactRead,
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.subject import SubjectReadMixin
from app.schemas.utils import make_update_schema


class UseIon(Schema):
    ion_name: str
    read: list[str] = []  # ruff:ignore[mutable-class-default]
    write: list[str] = []  # ruff:ignore[mutable-class-default]
    valence: int | None = None
    main_ion: bool | None = None


class NeuronBlock(Schema):
    global_: list[dict[str, str | None]] = Field(default=[], alias="global")
    range: list[dict[str, str | None]] = []  # ruff:ignore[mutable-class-default]
    useion: list[UseIon] = []  # ruff:ignore[mutable-class-default]
    nonspecific: list[dict[str, str | None]] = []  # ruff:ignore[mutable-class-default]


class IonChannelModelBaseMixin(NameDescriptionMixin):
    nmodl_suffix: str
    is_ljp_corrected: bool = False
    is_temperature_dependent: bool = False
    temperature_celsius: int | None
    is_stochastic: bool = False
    neuron_block: NeuronBlock
    conductance_name: str | None = None
    max_permeability_name: str | None = None


class IonChannelModelCreate(
    ScientificArtifactCreate,
    IonChannelModelBaseMixin,
):
    pass


IonChannelModelUserUpdate = make_update_schema(IonChannelModelCreate, "IonChannelModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
IonChannelModelAdminUpdate = make_update_schema(
    IonChannelModelCreate,
    "IonChannelModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class IonChannelModelRead(
    IonChannelModelBaseMixin,
    NestedScientificArtifactRead,
    SubjectReadMixin,
    BrainRegionReadMixin,
):
    pass


class IonChannelModelWAssets(
    IonChannelModelRead,
    AssetsMixin,
):
    pass


class IonChannelModelExpanded(
    IonChannelModelBaseMixin,
    ScientificArtifactRead,
):
    pass
