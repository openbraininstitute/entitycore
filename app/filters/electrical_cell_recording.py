from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import ElectricalCellRecording, EModel
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
    SubjectFilterMixin,
)


class _NestedEModelFilter(IdFilterMixin, CustomFilter):
    """Simplified EModel filter allowing to filter only by id and id__in."""

    class Constants(CustomFilter.Constants):
        model = EModel


class ElectricalCellRecordingFilter(
    CustomFilter, BrainRegionFilterMixin, SubjectFilterMixin, EntityFilterMixin, NameFilterMixin
):
    generated_emodel: Annotated[
        _NestedEModelFilter | None,
        FilterDepends(with_prefix("generated_emodel", _NestedEModelFilter)),
    ] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ElectricalCellRecording
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ElectricalCellRecordingFilterDep = Annotated[
    ElectricalCellRecordingFilter, FilterDepends(ElectricalCellRecordingFilter)
]
