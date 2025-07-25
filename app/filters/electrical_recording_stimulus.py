import uuid
from typing import Annotated

from app.db.model import ElectricalCellRecording
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    EntityFilterMixin,
    NameFilterMixin,
)
from app.filters.scientific_artifact import ScientificArtifactFilter


class ElectricalRecordingStimulusFilter(EntityFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    shape: str | None = None
    injection_type: str | None = None

    recording_id: uuid.UUID | None = None
    recording_id__in: list[uuid.UUID] | None = None

    class Constants(ScientificArtifactFilter.Constants):
        model = ElectricalCellRecording
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "shape",
            "injection_type",
        ]


ElectricalRecordingStimulusFilterDep = Annotated[
    ElectricalRecordingStimulusFilter, FilterDepends(ElectricalRecordingStimulusFilter)
]
