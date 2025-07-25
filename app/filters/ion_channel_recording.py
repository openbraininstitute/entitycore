from typing import Annotated

from app.db.model import IonChannelRecording
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    NameFilterMixin,
)
from app.filters.scientific_artifact import ScientificArtifactFilter


class IonChannelRecordingFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelRecording
        ordering_model_fields = [  # noqa: RUF012
            "ion_channel",
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
        ]


IonChannelRecordingFilterDep = Annotated[
    IonChannelRecordingFilter, FilterDepends(IonChannelRecordingFilter)
]
