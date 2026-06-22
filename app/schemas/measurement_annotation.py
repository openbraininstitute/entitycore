import uuid
from collections.abc import Sequence

from pydantic.json_schema import SkipJsonSchema

from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.db.utils import MeasurableEntityType
from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, NestedIdentifiableRead


class MeasurementItem(Schema):
    name: MeasurementStatistic | None
    unit: MeasurementUnit | None
    value: float | None


class MeasurementKindBase(Schema):
    structural_domain: StructuralDomain
    measurement_items: list[MeasurementItem]
    pref_label: str


class MeasurementKindRead(MeasurementKindBase):
    pass


class MeasurementKindCreate(MeasurementKindBase):
    # hidden in the schema because set in the create endpoint
    measurement_label_id: SkipJsonSchema[uuid.UUID | None] = None


class MeasurementAnnotationBase(Schema):
    entity_id: uuid.UUID
    entity_type: MeasurableEntityType


class MeasurementAnnotationRead(MeasurementAnnotationBase, NestedIdentifiableRead):
    entity_type: MeasurableEntityType
    measurement_kinds: Sequence[MeasurementKindRead]


class MeasurementAnnotationCreate(MeasurementAnnotationBase, IdentifiableCreate):
    measurement_kinds: Sequence[MeasurementKindCreate]


class MeasurementAnnotationUpdate(Schema):
    entity_id: uuid.UUID | None = None
    entity_type: MeasurableEntityType | None = None
    measurement_kinds: Sequence[MeasurementKindCreate] | None = None


MeasurementAnnotationUserUpdate = MeasurementAnnotationUpdate
MeasurementAnnotationAdminUpdate = MeasurementAnnotationUpdate
