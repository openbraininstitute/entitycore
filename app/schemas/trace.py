from pydantic import BaseModel, Field

from app.schemas.base import BrainLocationRead, CreationMixin, File
from app.schemas.singlecell_base import SingleCellData


class StimulusCreate(BaseModel):
    stimulus_id: int
    dt: float = Field(
        ...,
        title="Time Step (dt)",
        description="Time step for this stimulus, in ms.",
    )


class StimulusRead(StimulusCreate, CreationMixin):
    pass


# Trace Model for Electrophysiology Data
class TraceCreate(SingleCellData):
    file: File = Field(..., title="File", description="File associated with the trace.")
    ljp: float = Field(
        0.0,
        title="Liquid Junction Potential",
        description="Correction applied to the voltage trace, in mV",
    )
    stimuli: StimulusCreate = Field(
        ...,
        title="Stimuli",
        description="List of stimuli applied to the cell with their respective time steps",
    )
    recording_location: str = Field(
        ...,
        title="Recording Location",
        description="location on the cell where recording was performed, in hoc-compatible format",
    )
    comment: str | None = Field(
        "", title="Comment", description="Additional information or observations"
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
