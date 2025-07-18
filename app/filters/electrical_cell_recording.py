from typing import Annotated

from app.db.model import ElectricalCellRecording
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    NameFilterMixin,
)
from app.filters.subject import SubjectFilterMixin


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
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
            "etype__pref_label",
        ]


ElectricalCellRecordingFilterDep = Annotated[
    ElectricalCellRecordingFilter, FilterDepends(ElectricalCellRecordingFilter)
]
