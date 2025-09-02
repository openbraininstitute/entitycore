from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    ElectricalRecordingOrigin,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
)
from app.schemas.annotation import ETypeClassRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.electrical_recording_stimulus import NestedElectricalRecordingStimulusRead
from app.schemas.scientific_artifact import (
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


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


ElectricalCellRecordingUpdate = make_update_schema(
    ElectricalCellRecordingCreate, "ElectricalCellRecordingUpdate"
)


class ElectricalCellRecordingRead(
    ElectricalCellRecordingBase,
    ScientificArtifactRead,
    ContributionReadWithoutEntityMixin,
):
    stimuli: Annotated[
        list[NestedElectricalRecordingStimulusRead] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
    etypes: list[ETypeClassRead] | None
