import uuid

from enum import Enum, auto
from pydantic import BaseModel, ConfigDict
from typing import Literal
from app.db.types import PointLocationBase
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import MTypeClassRead
from app.schemas.asset import AssetsMixin
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
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.species import NestedSpeciesRead, NestedStrainRead
from app.db.types import RepairPipelineType, MorphologyGenerationType, SlicingDirectionType, StainingType, MethodsType


class ProtocolMixin(BaseModel):
        """Generic Experimental method.

    Parameters:
    -----------
    protocol_document: str, optional
        URL link to protocol document or publication
    protocol_design: str
        From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    """
    protocol_document: str | None = None
    protocol_design: str

class ExperimentalMorphologyProtocolRead(ProtocolMixin):
     """Experimental morphology method for capturing cell morphology data.

    Parameters:
    -----------
 
    staining_type: strenum
        Method used for staining
    slicing_thickness: float
        Thickness of the slice in microns
    slicing_direction: SlicingDirectionType, optional
        Direction of slicing
    magnification: float, optional
        Magnification level used
    tissue_shrinkage: float, optional
        Amount tissue shrunk by (not correction factor)
    has_been_corrected_for_shrinkage: bool, optional
        Whether data has been corrected for shrinkage
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
    method: MethodsType

class MorphologyProtocolRead(BaseModel):
    # This acts as a union type for reading different methods
    # Pydantic's discriminated unions would be ideal here if using Pydantic V2+
    # For V1, you might need to handle this with a custom root validator
    # or by having specific read schemas for each CellMorphology type.
    # For simplicity, we'll assume a "smart" client that knows how to parse based on 'type'.
    id: uuid.UUID
    type: MorphologyGenerationType #Literal["digital", "computational", "modified"]
    protocol_document: str | None = None
    protocol_design: str


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None
    morphology_generation_type: MorphologyGenerationType = MorphologyGenerationType.placeholder


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    legacy_id: list[str] | None = None
    morphology_genration_type: MorphologyGenerationType = MorphologyGenerationType.placeholder


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    legacy_id: list[str] | None = None
    morphology_generation_type: MorphologyGenerationType = MorphologyGenerationType.placeholder
    morphology_protocol_id: uuid.UUID | None = None # This would be set after the method is created

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
):
    species: NestedSpeciesRead
    strain: NestedStrainRead | None
    brain_region: BrainRegionRead
    mtypes: list[MTypeClassRead] | None
    morphology_protocol: MorphologyProtocolRead | None # Now references the polymorphic method

class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None


class DigitalReconstruction(CellMorphologyRead):
    reconstruction_method: ExperimentalMorphologyProtocol
    repair_pipeline_state: RepairPipelineType


class DigitalReconstructionCreate(CellMorphologyCreate):
    morphology_generation_type: Literal[MorphologyGenerationType.digital]
    reconstruction_method: ExperimentalMorphologyProtocol
    repair_pipeline_state: RepairPipelineType



class ModifiedReconstruction(CellMorphologyRead):
    method_description: ModifiedMorphologyProtocol


class ModifiedReconstructionCreate(CellMorphologyCreate):
    morphology_generation_type: Literal[MorphologyGenerationType.modified]
    method_description: ModifiedMorphologyProtocol


class ComputationallySynthesized(CellMorphologyRead):
    method_description: ComputationallySynthesizedMorphologyProtocol


class ComputationallySynthesizedCreate(CellMorphologyCreate):
    morphology_generation_type: Literal[MorphologyGenerationType.computational]
    method_description: ComputationallySynthesizedMorphologyProtocol


class Placeholder(CellMorphologyRead):
    pass


class PlaceholderCreate(CellMorphologyCreate):
    morphology_generation_type: Literal[MorphologyGenerationType.placeholder]

