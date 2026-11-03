from typing import Annotated

from pydantic import Field

from app.db.types import ElectricalRecordingOrigin, ElectricalRecordingType
from app.schemas.base import NameDescriptionMixin
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


class ExtracellularRecordingBase(NameDescriptionMixin):
    recording_type: Annotated[
        ElectricalRecordingType,
        Field(
            title="Recording Type",
            description=f"Recording type. One of: {sorted(ElectricalRecordingType)}",
        ),
    ] = ElectricalRecordingType.extracellular
    recording_origin: Annotated[
        ElectricalRecordingOrigin,
        Field(
            title="Recording Origin",
            description=f"Recording origin. One of: {sorted(ElectricalRecordingOrigin)}",
        ),
    ]
    probe_names: Annotated[
        list[str],
        Field(
            title="Probe Names",
            description="Names of the probes or electrode arrays, as in the NWB file.",
        ),
    ]
    channel_count: Annotated[
        int,
        Field(
            title="Channel Count",
            description="Number of recorded channels, over all probes.",
            gt=0,
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
    temperature: Annotated[
        float | None,
        Field(
            title="Temperature",
            description="Temperature at which the recording was performed, in degrees Celsius.",
        ),
    ] = None
    comment: Annotated[
        str | None,
        Field(
            title="Comment",
            description="Comment with further details.",
        ),
    ] = None


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
