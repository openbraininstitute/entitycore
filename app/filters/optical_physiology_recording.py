from app.db.model import OpticalPhysiologyRecording
from app.db.types import ImagingModality, OpticalRecordingOrigin
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class OpticalPhysiologyRecordingFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
    ILikeSearchFilterMixin,
):
    sampling_frequency: float | None = None
    sampling_frequency__lte: float | None = None
    sampling_frequency__gte: float | None = None
    duration__lte: float | None = None
    duration__gte: float | None = None
    imaging_modality: ImagingModality | None = None
    imaging_modality__in: list[ImagingModality] | None = None
    recording_origin: OpticalRecordingOrigin | None = None
    recording_origin__in: list[OpticalRecordingOrigin] | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(ScientificArtifactFilter.Constants):
        model = OpticalPhysiologyRecording
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
            "sampling_frequency",
            "duration",
            "imaging_modality",
            "recording_origin",
        ]
