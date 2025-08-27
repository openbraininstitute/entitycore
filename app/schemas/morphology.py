import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import (
    ModifiedMorphologyMethodType,
    MorphologyGenerationType,
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


class ProtocolMixin(BaseModel):
    """Generic Experimental method.

    Attributes:
        protocol_document: URL link to protocol document or publication.
        protocol_design: From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """

    protocol_document: str | None = None
    protocol_design: str


class ExperimentalMorphologyProtocolRead(ProtocolMixin):
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
    slicing_thickness: float
    slicing_direction: SlicingDirectionType | None = None
    magnification: float | None = None
    tissue_shrinkage: float | None = None
    corrected_for_shrinkage: bool | None = None


class ComputationallySynthesizedMorphologyProtocolRead(ProtocolMixin):
    id: uuid.UUID
    method: str


class ModifiedMorphologyProtocolRead(ProtocolMixin):
    id: uuid.UUID
    method: ModifiedMorphologyMethodType


class MorphologyProtocolRead(ProtocolMixin):
    id: uuid.UUID
    type: MorphologyGenerationType


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
