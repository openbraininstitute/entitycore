from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, TypeAdapter, field_validator

from app.db.types import (
    CellMorphologyGenerationType,
    CellMorphologyProtocolDesign,
    EntityType,
    ModifiedMorphologyMethodType,
    SlicingDirectionType,
    StainingType,
)
from app.schemas.base import (
    NameDescriptionMixin,
    Schema,
)
from app.schemas.entity import EntityCreate, EntityReadWoutAssets, NestedEntityBareRead
from app.schemas.types import SerializableHttpUrl
from app.schemas.utils import make_update_schema


class CellMorphologyProtocolMixin:
    """Generic Cell Morphology Protocol Mixin.

    Attributes:
        protocol_document: URL link to protocol document or publication.
        protocol_design: From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """

    protocol_document: SerializableHttpUrl | None = None
    protocol_design: CellMorphologyProtocolDesign


# Base Models


class CellMorphologyProtocolBaseMixin(NameDescriptionMixin):
    type: EntityType = EntityType.cell_morphology_protocol

    @field_validator("type")
    @classmethod
    def ensure_cell_morphology_protocol_type(cls, v: EntityType) -> EntityType:
        if v is not EntityType.cell_morphology_protocol:
            msg = "type must be cell_morphology_protocol"
            raise ValueError(msg)
        return v


class DigitalReconstructionCellMorphologyProtocolBase(
    CellMorphologyProtocolBaseMixin,
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
    CellMorphologyProtocolBaseMixin,
    CellMorphologyProtocolMixin,
):
    generation_type: Literal[CellMorphologyGenerationType.modified_reconstruction]
    method_type: ModifiedMorphologyMethodType


class ComputationallySynthesizedCellMorphologyProtocolBase(
    CellMorphologyProtocolBaseMixin,
    CellMorphologyProtocolMixin,
):
    generation_type: Literal[CellMorphologyGenerationType.computationally_synthesized]
    method_type: str


class PlaceholderCellMorphologyProtocolBase(
    CellMorphologyProtocolBaseMixin,
):
    generation_type: Literal[CellMorphologyGenerationType.placeholder]


# Create Models


class DigitalReconstructionCellMorphologyProtocolCreate(
    EntityCreate,
    DigitalReconstructionCellMorphologyProtocolBase,
):
    pass


class ModifiedReconstructionCellMorphologyProtocolCreate(
    EntityCreate,
    ModifiedReconstructionCellMorphologyProtocolBase,
):
    pass


class ComputationallySynthesizedCellMorphologyProtocolCreate(
    EntityCreate,
    ComputationallySynthesizedCellMorphologyProtocolBase,
):
    pass


class PlaceholderCellMorphologyProtocolCreate(
    EntityCreate,
    PlaceholderCellMorphologyProtocolBase,
):
    pass


# Update Models

USER_EXCLUDED_UPDATE_FIELDS = {"authorized_public"}
ADMIN_EXCLUDED_UPDATE_FIELDS = set()
PRESERVED_FIELDS = {"generation_type"}


DigitalReconstructionCellMorphologyProtocolUserUpdate = make_update_schema(
    DigitalReconstructionCellMorphologyProtocolCreate,
    "DigitalReconstructionCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ModifiedReconstructionCellMorphologyProtocolUserUpdate = make_update_schema(
    ModifiedReconstructionCellMorphologyProtocolCreate,
    "ModifiedReconstructionCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ComputationallySynthesizedCellMorphologyProtocolUserUpdate = make_update_schema(
    ComputationallySynthesizedCellMorphologyProtocolCreate,
    "ComputationallySynthesizedCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


PlaceholderCellMorphologyProtocolUserUpdate = make_update_schema(
    PlaceholderCellMorphologyProtocolCreate,
    "PlaceholderCellMorphologyProtocolUserUpdate",
    excluded_fields=USER_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


DigitalReconstructionCellMorphologyProtocolAdminUpdate = make_update_schema(
    DigitalReconstructionCellMorphologyProtocolCreate,
    "DigitalReconstructionCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ModifiedReconstructionCellMorphologyProtocolAdminUpdate = make_update_schema(
    ModifiedReconstructionCellMorphologyProtocolCreate,
    "ModifiedReconstructionCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


ComputationallySynthesizedCellMorphologyProtocolAdminUpdate = make_update_schema(
    ComputationallySynthesizedCellMorphologyProtocolCreate,
    "ComputationallySynthesizedCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


PlaceholderCellMorphologyProtocolAdminUpdate = make_update_schema(
    PlaceholderCellMorphologyProtocolCreate,
    "PlaceholderCellMorphologyProtocolAdminUpdate",
    excluded_fields=ADMIN_EXCLUDED_UPDATE_FIELDS,
    preserved_fields=PRESERVED_FIELDS,
)  # pyright : ignore [reportInvalidTypeForm]


# Read Models


class DigitalReconstructionCellMorphologyProtocolRead(
    EntityReadWoutAssets,
    DigitalReconstructionCellMorphologyProtocolBase,
):
    pass


class ModifiedReconstructionCellMorphologyProtocolRead(
    EntityReadWoutAssets,
    ModifiedReconstructionCellMorphologyProtocolBase,
):
    pass


class ComputationallySynthesizedCellMorphologyProtocolRead(
    EntityReadWoutAssets,
    ComputationallySynthesizedCellMorphologyProtocolBase,
):
    pass


class PlaceholderCellMorphologyProtocolRead(
    EntityReadWoutAssets,
    PlaceholderCellMorphologyProtocolBase,
):
    pass


# Nested Read Models


class NestedDigitalReconstructionCellMorphologyProtocolRead(
    NestedEntityBareRead,
    DigitalReconstructionCellMorphologyProtocolBase,
):
    pass


class NestedModifiedReconstructionCellMorphologyProtocolRead(
    NestedEntityBareRead,
    ModifiedReconstructionCellMorphologyProtocolBase,
):
    pass


class NestedComputationallySynthesizedCellMorphologyProtocolRead(
    NestedEntityBareRead,
    ComputationallySynthesizedCellMorphologyProtocolBase,
):
    pass


class NestedPlaceholderCellMorphologyProtocolRead(
    NestedEntityBareRead,
    PlaceholderCellMorphologyProtocolBase,
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

CellMorphologyProtocolUserUpdate = Annotated[
    DigitalReconstructionCellMorphologyProtocolUserUpdate
    | ModifiedReconstructionCellMorphologyProtocolUserUpdate
    | ComputationallySynthesizedCellMorphologyProtocolUserUpdate
    | PlaceholderCellMorphologyProtocolUserUpdate,
    Field(discriminator="generation_type"),
]

CellMorphologyProtocolAdminUpdate = Annotated[
    DigitalReconstructionCellMorphologyProtocolAdminUpdate
    | ModifiedReconstructionCellMorphologyProtocolAdminUpdate
    | ComputationallySynthesizedCellMorphologyProtocolAdminUpdate
    | PlaceholderCellMorphologyProtocolAdminUpdate,
    Field(discriminator="generation_type"),
]


class CellMorphologyProtocolReadAdapter(Schema):
    """Polymorphic wrapper for CellMorphologyProtocolRead."""

    _adapter: ClassVar[TypeAdapter] = TypeAdapter(CellMorphologyProtocolRead)

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> CellMorphologyProtocolRead:  # type: ignore[override]
        """Return the correct instance of the protocol."""
        return cls._adapter.validate_python(obj, *args, **kwargs)


class CellMorphologyProtocolUserUpdateAdapter(Schema):
    """Polymorphic wrapper for CellMorphologyProtocolUpdate."""

    _adapter: ClassVar[TypeAdapter] = TypeAdapter(CellMorphologyProtocolUserUpdate)

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> CellMorphologyProtocolUserUpdate:  # type: ignore[override]
        """Return the correct instance of the protocol."""
        model = cls._adapter.validate_python(obj, *args, **kwargs)
        # generation_type was needed only as a discriminator. It should not be updated.
        model.generation_type = None
        model.model_fields_set.discard("generation_type")  # make it unset
        return model
