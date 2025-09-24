from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

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
from app.schemas.utils import make_update_schema


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


# Update Models

PRESERVED_UPDATE_FIELDS = {"generation_type"}

USER_EXCLUDED_UPDATE_FIELDS = {
    "authorized_public",
}

DigitalReconstructionCellMorphologyProtocolUserUpdate = make_update_schema(
    DigitalReconstructionCellMorphologyProtocolCreate,
    "DigitalReconstructionCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ModifiedReconstructionCellMorphologyProtocolUserUpdate = make_update_schema(
    ModifiedReconstructionCellMorphologyProtocolCreate,
    "ModifiedReconstructionCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ComputationallySynthesizedCellMorphologyProtocolUserUpdate = make_update_schema(
    ComputationallySynthesizedCellMorphologyProtocolCreate,
    "ComputationallySynthesizedCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


PlaceholderCellMorphologyProtocolUserUpdate = make_update_schema(
    PlaceholderCellMorphologyProtocolCreate,
    "PlaceholderCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ADMIN_EXCLUDED_UPDATE_FIELDS = {}


DigitalReconstructionCellMorphologyProtocolAdminUpdate = make_update_schema(
    DigitalReconstructionCellMorphologyProtocolCreate,
    "DigitalReconstructionCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ModifiedReconstructionCellMorphologyProtocolAdminUpdate = make_update_schema(
    ModifiedReconstructionCellMorphologyProtocolCreate,
    "ModifiedReconstructionCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ComputationallySynthesizedCellMorphologyProtocolAdminUpdate = make_update_schema(
    ComputationallySynthesizedCellMorphologyProtocolCreate,
    "ComputationallySynthesizedCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


PlaceholderCellMorphologyProtocolAdminUpdate = make_update_schema(
    PlaceholderCellMorphologyProtocolCreate,
    "PlaceholderCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_UPDATE_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


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

type CellMorphologyProtocolUserUpdate = Annotated[
    DigitalReconstructionCellMorphologyProtocolUserUpdate
    | ModifiedReconstructionCellMorphologyProtocolUserUpdate
    | ComputationallySynthesizedCellMorphologyProtocolUserUpdate
    | PlaceholderCellMorphologyProtocolUserUpdate,
    Field(discriminator="generation_type"),
]

type CellMorphologyProtocolAdminUpdate = Annotated[
    DigitalReconstructionCellMorphologyProtocolAdminUpdate
    | ModifiedReconstructionCellMorphologyProtocolAdminUpdate
    | ComputationallySynthesizedCellMorphologyProtocolAdminUpdate
    | PlaceholderCellMorphologyProtocolAdminUpdate,
    Field(discriminator="generation_type"),
]


class CellMorphologyProtocolReadAdapter(BaseModel):
    """Polymorphic wrapper for CellMorphologyProtocolRead."""

    _adapter: ClassVar[TypeAdapter] = TypeAdapter(CellMorphologyProtocolRead)

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> CellMorphologyProtocolRead:  # type: ignore[override]
        """Return the correct instance of the protocol."""
        return cls._adapter.validate_python(obj, *args, **kwargs)
