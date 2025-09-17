from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    CellMorphologyGenerationType,
    CellMorphologyProtocolDesign,
    EntityType,
    ModifiedMorphologyMethodType,
    SlicingDirectionType,
    StainingType,
)
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.types import SerializableHttpUrl


class CommonReadMixin(
    IdentifiableMixin,
    CreationMixin,
    CreatedByUpdatedByMixin,
    AuthorizationMixin,
):
    """Common mixin for readable schemas."""


class CellMorphologyProtocolMixin:
    """Generic Cell Morphology Protocol Mixin.

    Attributes:
        protocol_document: URL link to protocol document or publication.
        protocol_design: From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """

    protocol_document: SerializableHttpUrl | None = None
    protocol_design: CellMorphologyProtocolDesign


# Base Models


class CellMorphologyProtocolBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: Literal[EntityType.cell_morphology_protocol] = EntityType.cell_morphology_protocol


class DigitalReconstructionCellMorphologyProtocolBase(
    CellMorphologyProtocolBase,
    CellMorphologyProtocolMixin,
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

    generation_type: Literal[CellMorphologyGenerationType.digital_reconstruction]
    staining_type: StainingType | None = None
    slicing_thickness: Annotated[float, Field(ge=0.0)]
    slicing_direction: SlicingDirectionType | None = None
    magnification: Annotated[float | None, Field(ge=0.0)] = None
    tissue_shrinkage: Annotated[float | None, Field(ge=0.0)] = None
    corrected_for_shrinkage: bool | None = None


class ModifiedReconstructionCellMorphologyProtocolBase(
    CellMorphologyProtocolBase,
    CellMorphologyProtocolMixin,
):
    generation_type: Literal[CellMorphologyGenerationType.modified_reconstruction]
    method_type: ModifiedMorphologyMethodType


class ComputationallySynthesizedCellMorphologyProtocolBase(
    CellMorphologyProtocolBase,
    CellMorphologyProtocolMixin,
):
    generation_type: Literal[CellMorphologyGenerationType.computationally_synthesized]
    method_type: str


class PlaceholderCellMorphologyProtocolBase(
    CellMorphologyProtocolBase,
):
    generation_type: Literal[CellMorphologyGenerationType.placeholder]


# Create Models


class DigitalReconstructionCellMorphologyProtocolCreate(
    DigitalReconstructionCellMorphologyProtocolBase,
    AuthorizationOptionalPublicMixin,
):
    pass


class ModifiedReconstructionCellMorphologyProtocolCreate(
    ModifiedReconstructionCellMorphologyProtocolBase,
    AuthorizationOptionalPublicMixin,
):
    pass


class ComputationallySynthesizedCellMorphologyProtocolCreate(
    ComputationallySynthesizedCellMorphologyProtocolBase,
    AuthorizationOptionalPublicMixin,
):
    pass


class PlaceholderCellMorphologyProtocolCreate(
    PlaceholderCellMorphologyProtocolBase,
    AuthorizationOptionalPublicMixin,
):
    pass


# Read Models


class DigitalReconstructionCellMorphologyProtocolRead(
    DigitalReconstructionCellMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class ModifiedReconstructionCellMorphologyProtocolRead(
    ModifiedReconstructionCellMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class ComputationallySynthesizedCellMorphologyProtocolRead(
    ComputationallySynthesizedCellMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


class PlaceholderCellMorphologyProtocolRead(
    PlaceholderCellMorphologyProtocolBase,
    CommonReadMixin,
):
    pass


# Nested Read Models


class NestedDigitalReconstructionCellMorphologyProtocolRead(
    DigitalReconstructionCellMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class NestedModifiedReconstructionCellMorphologyProtocolRead(
    ModifiedReconstructionCellMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class NestedComputationallySynthesizedCellMorphologyProtocolRead(
    ComputationallySynthesizedCellMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


class NestedPlaceholderCellMorphologyProtocolRead(
    PlaceholderCellMorphologyProtocolBase,
    IdentifiableMixin,
):
    pass


# Unions

type CellMorphologyProtocolCreate = Annotated[
    DigitalReconstructionCellMorphologyProtocolCreate
    | ModifiedReconstructionCellMorphologyProtocolCreate
    | ComputationallySynthesizedCellMorphologyProtocolCreate
    | PlaceholderCellMorphologyProtocolCreate,
    Field(discriminator="generation_type"),
]

type CellMorphologyProtocolRead = Annotated[
    DigitalReconstructionCellMorphologyProtocolRead
    | ModifiedReconstructionCellMorphologyProtocolRead
    | ComputationallySynthesizedCellMorphologyProtocolRead
    | PlaceholderCellMorphologyProtocolRead,
    Field(discriminator="generation_type"),
]

type NestedCellMorphologyProtocolRead = Annotated[
    NestedDigitalReconstructionCellMorphologyProtocolRead
    | NestedModifiedReconstructionCellMorphologyProtocolRead
    | NestedComputationallySynthesizedCellMorphologyProtocolRead
    | NestedPlaceholderCellMorphologyProtocolRead,
    Field(discriminator="generation_type"),
]
