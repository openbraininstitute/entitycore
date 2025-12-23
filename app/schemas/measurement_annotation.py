import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict
from pydantic.json_schema import SkipJsonSchema

from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.db.utils import MeasurableEntityType
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.utils import make_update_schema


class MeasurementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: MeasurementStatistic | None
    unit: MeasurementUnit | None
    value: float | None


class MeasurementKindBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    structural_domain: StructuralDomain
    measurement_items: list[MeasurementItem]
    pref_label: str


class MeasurementKindRead(MeasurementKindBase):
    pass


class MeasurementKindCreate(MeasurementKindBase):
    # hidden in the schema because set in the create endpoint
    measurement_label_id: SkipJsonSchema[uuid.UUID | None] = None


class MeasurementAnnotationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_id: uuid.UUID
    entity_type: MeasurableEntityType


class MeasurementAnnotationRead(MeasurementAnnotationBase, CreationMixin, IdentifiableMixin):
    entity_type: MeasurableEntityType
    measurement_kinds: Sequence[MeasurementKindRead]


class MeasurementAnnotationCreate(MeasurementAnnotationBase):
    measurement_kinds: Sequence[MeasurementKindCreate]


MeasurementAnnotationUserUpdate = make_update_schema(
    MeasurementAnnotationCreate,
    "MeasurementAnnotationUserUpdate",
)  # pyright : ignore [reportInvalidTypeForm]

MeasurementAnnotationAdminUpdate = make_update_schema(
    MeasurementAnnotationCreate,
    "MeasurementAnnotationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
