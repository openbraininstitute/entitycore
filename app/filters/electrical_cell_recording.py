from typing import Annotated

from app.db.model import ElectricalCellRecording
from app.dependencies.filter import FilterDepends
from app.filters.common import (
    ETypeClassFilterMixin,
    NameFilterMixin,
)
from app.filters.scientific_artifact import ScientificArtifactFilter


class ElectricalCellRecordingFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
    ETypeClassFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
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
