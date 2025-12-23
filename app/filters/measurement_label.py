from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import MeasurementLabel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    PrefLabelMixin,
)
from app.filters.person import CreatorFilterMixin


class NestedMeasurementLabelFilter(
    IdFilterMixin,
    PrefLabelMixin,
    CustomFilter,
):
    """MeasurementLabel filter with limited fields for nesting."""

    class Constants(CustomFilter.Constants):
        model = MeasurementLabel


class MeasurementLabelFilter(
    CreationFilterMixin,
    CreatorFilterMixin,
    NestedMeasurementLabelFilter,
):
    """Full MeasurementLabel filter."""

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedMeasurementLabelFilter.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "pref_label",
        ]


MeasurementLabelFilterDep = Annotated[MeasurementLabelFilter, FilterDepends(MeasurementLabelFilter)]
NestedMeasurementLabelFilterDep = FilterDepends(
    with_prefix("measurement_label", NestedMeasurementLabelFilter)
)
