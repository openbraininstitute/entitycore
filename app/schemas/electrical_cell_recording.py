import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    ElectricalRecordingOrigin,
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
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
)
from app.schemas.subject import SubjectRead


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
    brain_region_id: uuid.UUID | None = None


class ElectricalCellRecordingRead(
    ElectricalCellRecordingBase,
    CreationMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    EntityTypeMixin,
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
