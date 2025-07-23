from typing import Annotated

from pydantic import Field

from app.db.types import IonChannel
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schema.contribution import ElectricalCellRecordingBase, ElectricalRecordingStimulusRead
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)


class IonChannelRecordingBase(ElectricalCellRecordingBase):
    ion_channel: Annotated[
        IonChannel,
        Field(
            title="Ion Channel",
            description="The ion channel that was recorded from",
        ),
    ]
    cell_line: Annotated[
        str,
        Field(
            title="Cell Line",
            description="The cell line from which the ion channel was recorded",
        ),
    ]


class IonChannelRecordingCreate(IonChannelRecordingBase, ScientificArtifactCreate):
    pass


class IonChannelRecordingRead(
    IonChannelRecordingBase,
    ScientificArtifactRead,
    ContributionReadWithoutEntityMixin,
):
    stimuli: Annotated[
        list[ElectricalRecordingStimulusRead] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
