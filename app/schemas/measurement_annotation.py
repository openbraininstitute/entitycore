import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.utils.entity import MeasurableEntityType


class MeasurementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: MeasurementStatistic | None
    unit: MeasurementUnit | None
    value: float | None


class MeasurementKindBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pref_label: str
    definition: str | None = None
    structural_domain: StructuralDomain | None = None
    measurement_items: list[MeasurementItem]


class MeasurementAnnotationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_id: uuid.UUID
    entity_type: MeasurableEntityType
    measurement_kinds: Sequence[MeasurementKindBase]


class MeasurementAnnotationCreate(MeasurementAnnotationBase):
    pass


class MeasurementAnnotationRead(MeasurementAnnotationBase):
    id: uuid.UUID
