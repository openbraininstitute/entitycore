import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, model_validator

from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.utils.entity import MeasurableEntityType


class MeasurementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: MeasurementStatistic | None
    unit: MeasurementUnit | None
    value: float | None


class MeasurementKindBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    structural_domain: StructuralDomain | None = None
    measurement_items: list[MeasurementItem]
    pref_label: str


class MeasurementKindRead(MeasurementKindBase):
    pass


class MeasurementKindCreate(MeasurementKindBase):
    label_id: uuid.UUID | None = None  # assigned from pref_label if not set

    @model_validator(mode="after")
    def _require_label_id_or_pref_label(self):
        if not self.label_id and not self.pref_label:
            msg = "label_id or pref_label must be provided"
            raise ValueError(msg)
        if self.label_id and self.pref_label:
            msg = "label_id and pref_label are mutually exclusive"
            raise ValueError(msg)
        return self


class MeasurementAnnotationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_id: uuid.UUID
    entity_type: MeasurableEntityType


class MeasurementAnnotationRead(MeasurementAnnotationBase, CreationMixin, IdentifiableMixin):
    entity_type: MeasurableEntityType
    measurement_kinds: Sequence[MeasurementKindRead]


class MeasurementAnnotationCreate(MeasurementAnnotationBase):
    measurement_kinds: Sequence[MeasurementKindCreate]
