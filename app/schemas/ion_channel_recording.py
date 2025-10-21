import uuid
from typing import Annotated

from pydantic import Field

from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.electrical_cell_recording import ElectricalCellRecordingBase
from app.schemas.electrical_recording_stimulus import NestedElectricalRecordingStimulusRead
from app.schemas.ion_channel import NestedIonChannelRead
from app.schemas.scientific_artifact import (
    NestedScientificArtifactRead,
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


class IonChannelRecordingBase(ElectricalCellRecordingBase):
    cell_line: Annotated[
        str,
        Field(
            title="Cell Line",
            description="The cell line from which the ion channel was recorded",
        ),
    ]


class IonChannelRecordingCreate(
    IonChannelRecordingBase,
    ScientificArtifactCreate,
):
    ion_channel_id: Annotated[
        uuid.UUID,
        Field(
            title="Ion Channel ID",
            description="The id of the ion channel that was recorded from",
        ),
    ]


IonChannelRecordingUserUpdate = make_update_schema(
    IonChannelRecordingCreate, "IonChannelRecordingUserUpdate"
)  # pyright : ignore [reportInvalidTypeForm]

IonChannelRecordingAdminUpdate = make_update_schema(
    IonChannelRecordingCreate,
    "IonChannelRecordingAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelRecordingRead(
    IonChannelRecordingBase,
    NestedScientificArtifactRead,
):
    pass


class IonChannelRecordingRead(
    IonChannelRecordingBase,
    ScientificArtifactRead,
    ContributionReadWithoutEntityMixin,
):
    ion_channel: Annotated[
        NestedIonChannelRead,
        Field(
            title="Ion Channel",
            description="The ion channel that was recorded from",
        ),
    ]
    stimuli: Annotated[
        list[NestedElectricalRecordingStimulusRead] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
