from typing import List, Optional, Field

from app.schemas.base import BaseDataModel, SingleCellData, BrainLocationRead, CreationMixin, File


class StimulusCreate(BaseDataModel):
    stimulus_id: int
    dt: float = Field(
        ...,
        title="Time Step (dt)",
        description="Time step for this stimulus, in ms.",
    )


class StimulusRead(BaseDataModel, CreationMixin):
    pass


# Trace Model for Electrophysiology Data
class TraceCreate(SingleCellData):
    file: File = Field(..., title="File", description="File associated with the trace.")
    ljp: float = Field(
        0.0,
        title="Liquid Junction Potential",
        description="Correction applied to the voltage trace, in mV",
    )
    stimulus_id: List[tuple[int, float]] = Field(
        ..., title="Stimuli", description="List of stimuli applied to the cell"
    )
    recording_location: str = Field(
        ...,
        title="Recording Location",
        description="location on the cell where recording was performed, in hoc-compatible format",
    )
    comment: Optional[str] = Field(
        "", title="Comment", description="Additional information or observations"
    )
    derivation: Optional[int] = Field(
        None,
        title="Derivation ID",
        description="The ID of the cell or model the trace was derived from",
    )
    image: Optional[List[File]] = Field(
        None,
        title="Images",
        description="List of images associated with the trace.",
    )


class TraceRead(SingleCellData, CreationMixin):
    file: File
    ljp: float
    stimulus: List[StimulusRead]
    recording_location: BrainLocationRead
    comment: Optional[str]
    derivation: Optional[str]
