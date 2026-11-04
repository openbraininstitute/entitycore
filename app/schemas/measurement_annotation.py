import uuid
from collections.abc import Sequence
from typing import Annotated

from pydantic import MISSING
from pydantic.json_schema import SkipJsonSchema
from sqlalchemy.orm import Load, QueryableAttribute, selectinload

from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.db.utils import MeasurableEntityType
from app.schemas.base import ExpandableSchema, Schema
from app.schemas.expand import Expandable, expand_load
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


def _measurement_annotation_loader(
    parent: Load | None, attr: QueryableAttribute, _qualifiers: frozenset[str] | None
) -> list[Load]:
    """Load the measurement annotation of an entity, with its kinds, items and labels."""
    annotation_class = attr.property.mapper.class_
    kind_class = annotation_class.measurement_kinds.property.mapper.class_
    load = expand_load(parent, "joinedload", attr)
    # `entity_type` reads the annotated entity: at the root of the query it's the queried row
    entity_load = (
        load.contains_eager(annotation_class.entity)
        if parent is None
        else load.selectinload(annotation_class.entity)
    )
    return [
        load.selectinload(annotation_class.measurement_kinds).options(
            selectinload(kind_class.measurement_items),
            selectinload(kind_class.measurement_label),
        ),
        entity_load,
    ]


class MeasurementAnnotationReadMixin(ExpandableSchema):
    """Measurement annotation of a measurable entity, returned with `expand`."""

    measurement_annotation: Annotated[
        MeasurementAnnotationRead | MISSING | None,
        Expandable(loader=_measurement_annotation_loader),
    ] = MISSING


class MeasurementAnnotationCreate(MeasurementAnnotationBase, IdentifiableCreate):
    measurement_kinds: Sequence[MeasurementKindCreate]


class MeasurementAnnotationUpdate(Schema):
    entity_id: uuid.UUID | None = None
    entity_type: MeasurableEntityType | None = None
    measurement_kinds: Sequence[MeasurementKindCreate] | None = None


MeasurementAnnotationUserUpdate = MeasurementAnnotationUpdate
MeasurementAnnotationAdminUpdate = MeasurementAnnotationUpdate
