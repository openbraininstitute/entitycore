from typing import Annotated

from pydantic import Field

from app.db.types import ImagingModality, OpticalRecordingOrigin
from app.schemas.base import AuthorizedProjectIdMixin, NameDescriptionMixin
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


class OpticalPhysiologyRecordingBase(NameDescriptionMixin):
    sampling_frequency: Annotated[
        float,
        Field(
            title="Sampling Frequency",
            description="Frame rate per imaging plane, in Hz. Use 0 if not available.",
            ge=0.0,
        ),
    ]
    duration: Annotated[
        float,
        Field(
            title="Duration",
            description="Duration of the recording, in seconds. Use 0 if not available.",
            ge=0.0,
        ),
    ]
    imaging_modality: Annotated[
        ImagingModality,
        Field(
            title="Imaging Modality",
            description=f"Imaging modality. One of: {sorted(ImagingModality)}",
        ),
    ]
    recording_origin: Annotated[
        OpticalRecordingOrigin,
        Field(
            title="Recording Origin",
            description=f"Recording origin. One of: {sorted(OpticalRecordingOrigin)}",
        ),
    ]


class OpticalPhysiologyRecordingCreate(OpticalPhysiologyRecordingBase, ScientificArtifactCreate):
    pass


class OpticalPhysiologyRecordingAdminCreate(
    AuthorizedProjectIdMixin, OpticalPhysiologyRecordingCreate
):
    pass


OpticalPhysiologyRecordingUserUpdate = make_update_schema(
    OpticalPhysiologyRecordingCreate,
    "OpticalPhysiologyRecordingUserUpdate",
)  # pyright : ignore [reportInvalidTypeForm]

OpticalPhysiologyRecordingAdminUpdate = make_update_schema(
    OpticalPhysiologyRecordingCreate,
    "OpticalPhysiologyRecordingAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class OpticalPhysiologyRecordingRead(
    OpticalPhysiologyRecordingBase,
    ScientificArtifactRead,
    ContributionReadWithoutEntityMixin,
):
    pass
