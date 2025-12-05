import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import MeasurementStatistic, MeasurementUnit
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
    NameDescriptionMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.subject import SubjectReadMixin
from app.schemas.utils import make_update_schema


class MeasurementRecordBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: MeasurementStatistic
    unit: MeasurementUnit
    value: float


class MeasurementRecordCreate(MeasurementRecordBase):
    pass


class MeasurementRecordRead(MeasurementRecordBase):
    id: int


class ExperimentalDensityBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)


class ExperimentalDensityCreate(
    ExperimentalDensityBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    legacy_id: str | None
    measurements: list[MeasurementRecordCreate]


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
    measurements: list[MeasurementRecordRead]
    assets: list[AssetRead]
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


ExperimentalSynapsesPerConnectionUserUpdate = make_update_schema(
    ExperimentalSynapsesPerConnectionCreate, "ExperimentalSynapsesPerConnectionUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ExperimentalSynapsesPerConnectionAdminUpdate = make_update_schema(
    ExperimentalSynapsesPerConnectionCreate,
    "ExperimentalSynapsesPerConnectionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ExperimentalBoutonDensityUserUpdate = make_update_schema(
    ExperimentalBoutonDensityCreate, "ExperimentalBoutonDensityUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ExperimentalBoutonDensityAdminUpdate = make_update_schema(
    ExperimentalBoutonDensityCreate,
    "ExperimentalBoutonDensityAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ExperimentalNeuronDensityUserUpdate = make_update_schema(
    ExperimentalNeuronDensityCreate, "ExperimentalNeuronDensityUserUpdate"
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
