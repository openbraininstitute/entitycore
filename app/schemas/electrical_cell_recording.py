from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    ElectricalRecordingOrigin,
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
)
from app.schemas.annotation import ETypeClassRead
from app.schemas.base import (
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)


class ElectricalRecordingStimulusRead(CreationMixin, IdentifiableMixin, EntityTypeMixin):
    name: str
    description: str
    dt: float | None = None
    injection_type: ElectricalRecordingStimulusType
    shape: ElectricalRecordingStimulusShape
    start_time: float | None = None
    end_time: float | None = None


class ElectricalCellRecordingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    ljp: Annotated[
        float,
        Field(
            title="Liquid Junction Potential",
            description="Correction applied to the voltage trace, in mV",
        ),
    ] = 0.0
    recording_location: Annotated[
        list[str],
        Field(
            title="Recording Location",
            description=(
                "Location on the cell where recording was performed, in hoc-compatible format."
            ),
        ),
    ]
    recording_type: Annotated[
        ElectricalRecordingType,
        Field(
            title="Recording Type",
            description=f"Recording type. One of: {sorted(ElectricalRecordingStimulusType)}",
        ),
    ]
    recording_origin: Annotated[
        ElectricalRecordingOrigin,
        Field(
            title="Recording Origin",
            description=f"Recording origin. One of: {sorted(ElectricalRecordingOrigin)}",
        ),
    ]
    temperature: Annotated[
        float | None,
        Field(
            title="Temperature",
            description="Temperature at which the recording was performed, in degrees Celsius.",
        ),
    ] = None
    holding_current: Annotated[
        float,
        Field(
            title="Holding Current",
            description="Holding current applied during the recording, in nA.",
        ),
    ]
    comment: Annotated[
        str | None,
        Field(
            title="Comment",
            description="Comment with further details.",
        ),
    ] = None
    legacy_id: list[str] | None = None


class ElectricalCellRecordingCreate(ElectricalCellRecordingBase, ScientificArtifactCreate):
    pass


class ElectricalCellRecordingRead(
    ElectricalCellRecordingBase,
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
    etypes: list[ETypeClassRead] | None
