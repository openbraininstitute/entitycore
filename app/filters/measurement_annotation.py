import uuid
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix
from pydantic import model_validator

from app.db.model import MeasurementAnnotation, MeasurementItem, MeasurementKind
from app.db.types import MeasurementStatistic, MeasurementUnit, StructuralDomain
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin
from app.utils.entity import MeasurableEntityType


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
    is_active: bool | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedMeasurementAnnotationFilter.Constants):
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012

    @model_validator(mode="after")
    def _entity_type_mandatory_with_is_active(self):
        """The field entity_type must be provided when the field is_active is provided."""
        if self.is_active is not None and self.entity_type is None:
            msg = "entity_type must be provided when is_active is provided"
            raise ValueError(msg)
        return self


MeasurementAnnotationFilterDep = Annotated[
    MeasurementAnnotationFilter, FilterDepends(MeasurementAnnotationFilter)
]
NestedMeasurementAnnotationFilterDep = FilterDepends(
    with_prefix("measurement_annotation", NestedMeasurementAnnotationFilter)
)
