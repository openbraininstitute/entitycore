import uuid
from typing import Annotated

from app.db.model import MeasurementAnnotation, MeasurementItem, MeasurementKind
from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.db.utils import MeasurableEntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin


class MeasurementItemFilter(CustomFilter):
    name: MeasurementStatistic | None = None
    unit: MeasurementUnit | None = None
    value__gte: float | None = None
    value__lte: float | None = None

    class Constants(CustomFilter.Constants):
        model = MeasurementItem


class MeasurementKindFilter(CustomFilter):
    pref_label: str | None = None
    structural_domain: StructuralDomain | None = None
    measurement_item: MeasurementItemFilter | None = None

    class Constants(CustomFilter.Constants):
        model = MeasurementKind


class NestedMeasurementAnnotationFilter(
    CustomFilter,
    CreationFilterMixin,
):
    measurement_kind: MeasurementKindFilter | None = None

    class Constants(CustomFilter.Constants):
        model = MeasurementAnnotation


class MeasurementAnnotationFilter(NestedMeasurementAnnotationFilter):
    id__in: list[uuid.UUID] | None = None
    entity_id: uuid.UUID | None = None
    entity_type: MeasurableEntityType | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(NestedMeasurementAnnotationFilter.Constants):
        ordering_model_fields = ["creation_date", "update_date"]  # ruff:ignore[mutable-class-default]


MeasurementAnnotationFilterDep = Annotated[
    MeasurementAnnotationFilter, FilterDepends(MeasurementAnnotationFilter)
]


class MeasurableFilterMixin:
    measurement_annotation: NestedMeasurementAnnotationFilter | None = None
