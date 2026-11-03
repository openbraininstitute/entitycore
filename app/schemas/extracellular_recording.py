from typing import Annotated

from pydantic import Field

from app.db.types import ElectricalRecordingOrigin
from app.schemas.base import NameDescriptionMixin
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


class ExtracellularRecordingBase(NameDescriptionMixin):
    recording_origin: Annotated[
        ElectricalRecordingOrigin,
        Field(
            title="Recording Origin",
            description=f"Recording origin. One of: {sorted(ElectricalRecordingOrigin)}",
        ),
    ]
    sampling_frequency: Annotated[
        float,
        Field(
            title="Sampling Frequency",
            description="Sampling frequency of the raw traces, in Hz.",
            gt=0.0,
        ),
    ]
    duration: Annotated[
        float,
        Field(
            title="Duration",
            description="Duration of the recording, in seconds.",
            gt=0.0,
        ),
    ]


class ExtracellularRecordingCreate(ExtracellularRecordingBase, ScientificArtifactCreate):
    pass


ExtracellularRecordingUserUpdate = make_update_schema(
    ExtracellularRecordingCreate,
    "ExtracellularRecordingUserUpdate",
)  # pyright : ignore [reportInvalidTypeForm]

ExtracellularRecordingAdminUpdate = make_update_schema(
    ExtracellularRecordingCreate,
    "ExtracellularRecordingAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class ExtracellularRecordingRead(
    ExtracellularRecordingBase,
    ScientificArtifactRead,
    ContributionReadWithoutEntityMixin,
):
    pass
