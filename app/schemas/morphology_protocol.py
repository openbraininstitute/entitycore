from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    EntityType,
    ModifiedMorphologyMethodType,
    MorphologyGenerationType,
    MorphologyProtocolDesign,
    SlicingDirectionType,
    StainingType,
)
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import AuthorizationMixin, CreationMixin, IdentifiableMixin
from app.schemas.types import SerializableHttpUrl


class CommonReadMixin(
    IdentifiableMixin,
    CreationMixin,
    CreatedByUpdatedByMixin,
    AuthorizationMixin,
):
    """Common mixin for readable schemas."""


class ProtocolMixin:
    """Generic Protocol Mixin.

    Attributes:
        protocol_document: URL link to protocol document or publication.
        protocol_design: From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """

    protocol_document: SerializableHttpUrl | None = None
    protocol_design: MorphologyProtocolDesign


class MorphologyProtocolBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: Literal[EntityType.morphology_protocol] = EntityType.morphology_protocol


class DigitalReconstructionMorphologyProtocolBase(
    MorphologyProtocolBase,
    ProtocolMixin,
):
    """Experimental morphology method for capturing cell morphology data.

    Attributes:
        staining_type: Method used for staining.
        slicing_thickness: Thickness of the slice in microns.
        slicing_direction: Direction of slicing.
        magnification: Magnification level used.
        tissue_shrinkage: Amount tissue shrunk by (not correction factor).
        corrected_for_shrinkage: Whether data has been corrected for shrinkage.
    """

    generation_type: Literal[MorphologyGenerationType.digital_reconstruction]
    staining_type: StainingType | None = None
    slicing_thickness: Annotated[float, Field(ge=0.0, le=1000.0)]
    slicing_direction: SlicingDirectionType | None = None
    magnification: Annotated[float | None, Field(ge=0.0)] = None
    tissue_shrinkage: Annotated[float | None, Field(ge=0.0)] = None
    corrected_for_shrinkage: bool | None = None


class ModifiedReconstructionMorphologyProtocolBase(
    MorphologyProtocolBase,
    ProtocolMixin,
):
    generation_type: Literal[MorphologyGenerationType.modified_reconstruction]
    method: ModifiedMorphologyMethodType


class ComputationallySynthesizedMorphologyProtocolBase(
    MorphologyProtocolBase,
    ProtocolMixin,
):
    generation_type: Literal[MorphologyGenerationType.computationally_synthesized]
    method: str


class PlaceholderMorphologyProtocolBase(
    MorphologyProtocolBase,
):
    generation_type: Literal[MorphologyGenerationType.placeholder]


class DigitalReconstructionMorphologyProtocolCreate(
    DigitalReconstructionMorphologyProtocolBase,
):
    pass


class NestedDigitalReconstructionMorphologyProtocolRead(
    DigitalReconstructionMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class DigitalReconstructionMorphologyProtocolRead(
    DigitalReconstructionMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class ModifiedReconstructionMorphologyProtocolCreate(
    ModifiedReconstructionMorphologyProtocolBase,
):
    pass


class NestedModifiedReconstructionMorphologyProtocolRead(
    ModifiedReconstructionMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class ModifiedReconstructionMorphologyProtocolRead(
    ModifiedReconstructionMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class ComputationallySynthesizedMorphologyProtocolCreate(
    ComputationallySynthesizedMorphologyProtocolBase,
):
    pass


class NestedComputationallySynthesizedMorphologyProtocolRead(
    ComputationallySynthesizedMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class ComputationallySynthesizedMorphologyProtocolRead(
    ComputationallySynthesizedMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class PlaceholderMorphologyProtocolCreate(
    PlaceholderMorphologyProtocolBase,
):
    pass


class NestedPlaceholderMorphologyProtocolRead(
    PlaceholderMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class PlaceholderMorphologyProtocolRead(
    PlaceholderMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


type MorphologyProtocolCreate = Annotated[
    DigitalReconstructionMorphologyProtocolCreate
    | ModifiedReconstructionMorphologyProtocolCreate
    | ComputationallySynthesizedMorphologyProtocolCreate
    | PlaceholderMorphologyProtocolCreate,
    Field(discriminator="generation_type"),
]

type MorphologyProtocolRead = Annotated[
    DigitalReconstructionMorphologyProtocolRead
    | ModifiedReconstructionMorphologyProtocolRead
    | ComputationallySynthesizedMorphologyProtocolRead
    | PlaceholderMorphologyProtocolRead,
    Field(discriminator="generation_type"),
]

type NestedMorphologyProtocolRead = Annotated[
    NestedDigitalReconstructionMorphologyProtocolRead
    | NestedModifiedReconstructionMorphologyProtocolRead
    | NestedComputationallySynthesizedMorphologyProtocolRead
    | NestedPlaceholderMorphologyProtocolRead,
    Field(discriminator="generation_type"),
]
