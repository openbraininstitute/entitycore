from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ElectricalCellRecording
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilterMixin,
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
    MTypeClassFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ElectricalCellRecording
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ElectricalCellRecordingFilterDep = Annotated[
    ElectricalCellRecordingFilter, FilterDepends(ElectricalCellRecordingFilter)
]
