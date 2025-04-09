import uuid
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import MeasurementAnnotation, MeasurementItem, MeasurementKind
from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin


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
    pref_label: str | None = None
    definition: str | None = None
    structural_domain: StructuralDomain | None = None
    measurement_item: Annotated[MeasurementItemFilter | None, NestedMeasurementItemFilterDep] = None

    class Constants(CustomFilter.Constants):
        model = MeasurementKind


NestedMeasurementKindFilterDep = FilterDepends(
    with_prefix("measurement_kind", MeasurementKindFilter)
)


class MeasurementAnnotationFilter(
    CustomFilter,
    CreationFilterMixin,
):
    id__in: list[uuid.UUID] | None = None
    entity_id: uuid.UUID | None = None
    measurement_kind: Annotated[MeasurementKindFilter | None, NestedMeasurementKindFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MeasurementAnnotation
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


MeasurementAnnotationFilterDep = Annotated[
    MeasurementAnnotationFilter, FilterDepends(MeasurementAnnotationFilter)
]
NestedMeasurementAnnotationFilterDep = FilterDepends(
    with_prefix("measurement_annotation", MeasurementAnnotationFilter)
)
