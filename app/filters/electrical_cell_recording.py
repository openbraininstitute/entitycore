from typing import Annotated

from app.db.model import ElectricalCellRecording
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    NameFilterMixin,
    SubjectFilterMixin,
)


class ElectricalCellRecordingFilter(
    CustomFilter,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
    ETypeClassFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ElectricalCellRecording
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ElectricalCellRecordingFilterDep = Annotated[
    ElectricalCellRecordingFilter, FilterDepends(ElectricalCellRecordingFilter)
]
