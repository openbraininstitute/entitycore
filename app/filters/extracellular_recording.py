from typing import Annotated

from app.db.model import ExtracellularRecording
from app.db.types import ElectricalRecordingOrigin, ElectricalRecordingType
from app.dependencies.filter import FilterDepends
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class ExtracellularRecordingFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
    ILikeSearchFilterMixin,
):
    recording_type: ElectricalRecordingType | None = None
    recording_type__in: list[ElectricalRecordingType] | None = None
    recording_origin: ElectricalRecordingOrigin | None = None
    recording_origin__in: list[ElectricalRecordingOrigin] | None = None
    channel_count: int | None = None
    channel_count__lte: int | None = None
    channel_count__gte: int | None = None
    sampling_frequency: float | None = None
    sampling_frequency__lte: float | None = None
    sampling_frequency__gte: float | None = None
    duration__lte: float | None = None
    duration__gte: float | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(ScientificArtifactFilter.Constants):
        model = ExtracellularRecording
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
            "channel_count",
            "sampling_frequency",
            "duration",
        ]


ExtracellularRecordingFilterDep = Annotated[
    ExtracellularRecordingFilter, FilterDepends(ExtracellularRecordingFilter)
]
