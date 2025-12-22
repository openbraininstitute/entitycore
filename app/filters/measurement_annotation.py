import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import MeasurementAnnotation, MeasurementItem, MeasurementKind
from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.db.utils import MeasurableEntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin
from app.filters.measurement_label import (
    NestedMeasurementLabelFilter,
    NestedMeasurementLabelFilterDep,
)


class MeasurementItemFilter(CustomFilter):
    name: MeasurementStatistic | None = None
    unit: MeasurementUnit | None = None
    value__gte: float | None = None
    value__lte: float | None = None

    class Constants(CustomFilter.Constants):
        model = MeasurementItem


NestedMeasurementItemFilterDep = FilterDepends(
    with_prefix("measurement_item", MeasurementItemFilter)
)


class MeasurementKindFilter(CustomFilter):
    structural_domain: StructuralDomain | None = None
    measurement_item: Annotated[MeasurementItemFilter | None, NestedMeasurementItemFilterDep] = None
    measurement_label: Annotated[
        NestedMeasurementLabelFilter | None, NestedMeasurementLabelFilterDep
    ] = None

    class Constants(CustomFilter.Constants):
        model = MeasurementKind


NestedMeasurementKindFilterDep = FilterDepends(
    with_prefix("measurement_kind", MeasurementKindFilter)
)


class NestedMeasurementAnnotationFilter(
    CustomFilter,
    CreationFilterMixin,
):
    measurement_kind: Annotated[MeasurementKindFilter | None, NestedMeasurementKindFilterDep] = None

    class Constants(CustomFilter.Constants):
        model = MeasurementAnnotation


class MeasurementAnnotationFilter(NestedMeasurementAnnotationFilter):
    id__in: list[uuid.UUID] | None = None
    entity_id: uuid.UUID | None = None
    entity_type: MeasurableEntityType | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedMeasurementAnnotationFilter.Constants):
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


MeasurementAnnotationFilterDep = Annotated[
    MeasurementAnnotationFilter, FilterDepends(MeasurementAnnotationFilter)
]
NestedMeasurementAnnotationFilterDep = FilterDepends(
    with_prefix("measurement_annotation", NestedMeasurementAnnotationFilter)
)


class MeasurableFilterMixin:
    measurement_annotation: Annotated[
        NestedMeasurementAnnotationFilter | None, NestedMeasurementAnnotationFilterDep
    ] = None
