import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import ElectricalRecordingType
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


class StimulusCreate(BaseModel):
    stimulus_id: int
    dt: float = Field(
        ...,
        title="Time Step (dt)",
        description="Time step for this stimulus, in ms.",
    )


class StimulusRead(StimulusCreate, CreationMixin):
    pass


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
    legacy_id: list[str] | None = None


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


"""
# Trace Model for Electrophysiology Data
class TraceCreate(SingleCellData):
    file: File = Field(..., title="File", description="File associated with the trace.")
    stimuli: StimulusCreate = Field(
        ...,
        title="Stimuli",
        description="List of stimuli applied to the cell with their respective time steps",
    )
    derivation: int | None = Field(
        None,
        title="Derivation ID",
        description="The ID of the cell or model the trace was derived from",
    )
    image: list[File] | None = Field(
        None,
        title="Images",
        description="List of images associated with the trace.",
    )


class TraceRead(SingleCellData, CreationMixin):
    file: File
    ljp: float
    stimulus: list[StimulusRead]
    recording_location: BrainLocationRead
    comment: str | None
    derivation: str | None

"""
