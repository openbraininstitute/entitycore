from typing import Annotated

from app.db.model import IonChannelRecording
from app.db.types import ElectricalRecordingOrigin, ElectricalRecordingType
from app.dependencies.filter import FilterDepends
from app.filters.common import NameFilterMixin
from app.filters.ion_channel import NestedIonChannelFilter, NestedIonChannelFilterDep
from app.filters.scientific_artifact import ScientificArtifactFilter


class IonChannelRecordingFilter(ScientificArtifactFilter, NameFilterMixin):
    recording_type: ElectricalRecordingType | None = None
    recording_type__in: list[ElectricalRecordingType] | None = None
    recording_origin: ElectricalRecordingOrigin | None = None
    recording_origin__in: list[ElectricalRecordingOrigin] | None = None
    temperature: float | None = None
    ion_channel: Annotated[NestedIonChannelFilter | None, NestedIonChannelFilterDep] = None
    cell_line: str

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = IonChannelRecording
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
            "ion_channel__name",
            "ion_channel__label",
            "ion_channel__gene",
        ]


IonChannelRecordingFilterDep = Annotated[
    IonChannelRecordingFilter, FilterDepends(IonChannelRecordingFilter)
]
