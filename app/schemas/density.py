import uuid

from app.db.types import MeasurementStatistic, MeasurementUnit
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    NameDescriptionMixin,
    Schema,
)
from app.schemas.brain_region import (
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    NestedBrainRegionRead,
)
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.license import LicensedCreateMixin, LicensedReadMixin
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin
from app.schemas.utils import make_update_schema


class MeasurementRecordBase(Schema):
    name: MeasurementStatistic
    unit: MeasurementUnit
    value: float


class MeasurementRecordCreate(MeasurementRecordBase):
    pass


class MeasurementRecordRead(MeasurementRecordBase):
    id: int


class ExperimentalDensityBaseMixin(NameDescriptionMixin):
    pass


class ExperimentalDensityCreate(
    ExperimentalDensityBaseMixin,
    LicensedCreateMixin,
    BrainRegionCreateMixin,
    SubjectCreateMixin,
    EntityCreate,
):
    legacy_id: str | None
    measurements: list[MeasurementRecordCreate]


class ExperimentalDensityRead(
    ExperimentalDensityBaseMixin,
    EntityRead,
    LicensedReadMixin,
    SubjectReadMixin,
    BrainRegionReadMixin,
):
    measurements: list[MeasurementRecordRead]


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
    pre_region: NestedBrainRegionRead
    post_region: NestedBrainRegionRead
