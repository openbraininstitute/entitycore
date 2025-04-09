import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
)
from app.schemas.asset import AssetRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    SubjectRead,
)


class ElectricalRecordingStimulusRead(CreationMixin, IdentifiableMixin):
    name: str
    description: str
    dt: float | None = None
    stimulus_injection_type: ElectricalRecordingStimulusType
    stimulus_shape: ElectricalRecordingStimulusShape
    stimulus_start_time: float | None = None
    stimulus_end_time: float | None = None


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
    recordingLocation: Annotated[
        list[str],
        Field(
            title="Recording Location",
            description=(
                "location on the cell where recording was performed, in hoc-compatible format"
            ),
        ),
    ]
    recordingType: Annotated[
        ElectricalRecordingType,
        Field(
            title="Recording Type",
            description="Recording type. One of intracellular|extracellular|both.",
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


class ElectricalCellRecordingCreate(
    ElectricalCellRecordingBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    subject_id: uuid.UUID
    brain_region_id: int | None = None


class ElectricalCellRecordingRead(
    ElectricalCellRecordingBase,
    CreationMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
):
    subject: SubjectRead
    brain_region: BrainRegionRead
    assets: list[AssetRead] | None
    stimuli: Annotated[
        list[ElectricalRecordingStimulusRead] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
