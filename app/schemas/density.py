import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import MeasurementUnit
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.asset import AssetRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.subject import SubjectReadMixin
from app.schemas.utils import make_update_schema


class MeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    unit: MeasurementUnit
    value: float


class ExperimentalDensityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str


class ExperimentalDensityCreate(
    ExperimentalDensityBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    legacy_id: str | None


class ExperimentalDensityRead(
    ExperimentalDensityBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    SubjectReadMixin,
):
    measurements: list[MeasurementRead] | None
    assets: list[AssetRead] | None
    brain_region: BrainRegionRead


class ExperimentalNeuronDensityCreate(ExperimentalDensityCreate):
    pass


class ExperimentalBoutonDensityCreate(ExperimentalDensityCreate):
    pass


class ExperimentalSynapsesPerConnectionCreate(ExperimentalDensityCreate):
    pre_mtype_id: uuid.UUID
    post_mtype_id: uuid.UUID
    pre_region_id: uuid.UUID
    post_region_id: uuid.UUID


ExperimentalSynapsesPerConnectionUpdate = make_update_schema(
    ExperimentalSynapsesPerConnectionCreate, "ExperimentalSynapsesPerConnectionUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ExperimentalSynapsesPerConnectionAdminUpdate = make_update_schema(
    ExperimentalSynapsesPerConnectionCreate,
    "ExperimentalSynapsesPerConnectionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ExperimentalBoutonDensityUpdate = make_update_schema(
    ExperimentalBoutonDensityCreate, "ExperimentalBoutonDensityUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ExperimentalBoutonDensityAdminUpdate = make_update_schema(
    ExperimentalBoutonDensityCreate,
    "ExperimentalBoutonDensityAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ExperimentalNeuronDensityUpdate = make_update_schema(
    ExperimentalNeuronDensityCreate, "ExperimentalNeuronDensityUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ExperimentalNeuronDensityAdminUpdate = make_update_schema(
    ExperimentalNeuronDensityCreate,
    "ExperimentalNeuronDensityAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class ExperimentalNeuronDensityRead(ExperimentalDensityRead):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None


class ExperimentalBoutonDensityRead(ExperimentalDensityRead):
    mtypes: list[MTypeClassRead] | None


class ExperimentalSynapsesPerConnectionRead(ExperimentalDensityRead):
    pre_mtype: MTypeClassRead
    post_mtype: MTypeClassRead
    pre_region: BrainRegionRead
    post_region: BrainRegionRead
