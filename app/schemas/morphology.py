import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import (
    EntityType,
    ModifiedMorphologyMethodType,
    MorphologyGenerationType,
    MorphologyProtocolDesign,
    PointLocationBase,
    SlicingDirectionType,
    StainingType,
)
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import MTypeClassRead
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.subject import SubjectReadMixin
from app.schemas.types import SerializableHttpUrl


class ProtocolMixin:
    """Generic Protocol Mixin.

    Attributes:
        protocol_document: URL link to protocol document or publication.
        protocol_design: From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """

    protocol_document: SerializableHttpUrl | None = None
    protocol_design: MorphologyProtocolDesign


class MorphologyProtocolRead(BaseModel):
    id: uuid.UUID
    type: Literal[EntityType.morphology_protocol]
    generation_type: MorphologyGenerationType


class DigitalReconstructionMorphologyProtocolRead(MorphologyProtocolRead, ProtocolMixin):
    """Experimental morphology method for capturing cell morphology data.

    Attributes:
        staining_type: Method used for staining.
        slicing_thickness: Thickness of the slice in microns.
        slicing_direction: Direction of slicing.
        magnification: Magnification level used.
        tissue_shrinkage: Amount tissue shrunk by (not correction factor).
        corrected_for_shrinkage: Whether data has been corrected for shrinkage.
    """

    id: uuid.UUID
    staining_type: StainingType | None = None
    slicing_thickness: Annotated[float, Field(ge=0.0, le=1000.0)]
    slicing_direction: SlicingDirectionType | None = None
    magnification: Annotated[float | None, Field(ge=0.0)] = None
    tissue_shrinkage: Annotated[float | None, Field(ge=0.0)] = None
    corrected_for_shrinkage: bool | None = None


class ModifiedReconstructionMorphologyProtocolRead(
    MorphologyProtocolRead,
    ProtocolMixin,
):
    method: ModifiedMorphologyMethodType


class ComputationallySynthesizedMorphologyProtocolRead(
    MorphologyProtocolRead,
    ProtocolMixin,
):
    method: str


class PlaceholderMorphologyProtocolRead(
    MorphologyProtocolRead,
):
    pass


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None = None


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    morphology_protocol_id: uuid.UUID | None = None


class CellMorphologyRead(
    CellMorphologyBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    AssetsMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    SubjectReadMixin,
    BrainRegionReadMixin,
):
    mtypes: list[MTypeClassRead] | None


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None
    morphology_protocol: MorphologyProtocolRead | None
