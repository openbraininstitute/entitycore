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
from app.db.types import PipelineType, MorphologyStructureType


class Protocol(BaseModel):
    """Generic Experimental method.

    Parameters:
    -----------
    protocol_document: str, optional
        URL link to protocol document or publication
    """

    protocol_document: str | None = None


class ExperimentalMorphologyMethod(Protocol):
    """Experimental morphology method for capturing cell morphology data.

    Parameters:
    -----------
    protocol_design: str
        From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    staining_method: str
        Method used for staining
    slicing_thickness: float
        Thickness of the slice in microns
    slicing_direction: str, optional
        Direction of slicing
    magnification: float, optional
        Magnification level used
    tissue_shrinkage: float, optional
        Amount tissue shrunk by (not correction factor)
    has_been_corrected_for_shrinkage: bool, optional
        Whether data has been corrected for shrinkage
    """

    protocol_design: str
    staining_method: str
    slicing_thickness: float

    slicing_direction: str | None = None
    magnification: float | None = None
    tissue_shrinkage: float | None = None
    has_been_corrected_for_shrinkage: bool | None = None

    class Config:
        from_attributes = True


class ComputationallySynthesizedMorphologyMethod(Protocol):
    method: str


class ModifiedMorphologyMethod(Protocol):
    method: MethodsType


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None
    morphology_structure_type: MorphologyStructureType = MorphologyStructureType.GENERIC


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    legacy_id: list[str] | None = None
    morphology_structure_type: MorphologyStructureType = MorphologyStructureType.GENERIC


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


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None


class ScoreDict(BaseModel):
    x: dict[str, float]


class MethodsType(Enum):
    Cloned = auto()
    Mix_and_match = auto()
    Mousified = auto()
    Ratified = auto()


class DigitalReconstruction(CellMorphologyRead):
    reconstruction_method: ExperimentalMorphologyMethod
    pipeline_state: PipelineType
    is_related_to: list[uuid.UUID]


class DigitalReconstructionCreate(CellMorphologyCreate):
    morphology_structure_type: Literal[MorphologyStructureType.DIGITAL]
    reconstruction_method: ExperimentalMorphologyMethod
    pipeline_state: PipelineType
    is_related_to: list[uuid.UUID]


class ModifiedReconstruction(CellMorphologyRead):
    method_description: ModifiedMorphologyMethod
    is_related_to: list[uuid.UUID]


class ModifiedReconstructionCreate(CellMorphologyCreate):
    morphology_structure_type: Literal[MorphologyStructureType.MODIFIED]
    method_description: ModifiedMorphologyMethod
    is_related_to: list[uuid.UUID]


class ComputationallySynthesized(CellMorphologyRead):
    method_description: ComputationallySynthesizedMorphologyMethod
    score_dict: ScoreDict
    provenance: ScoreDict


class ComputationallySynthesizedCreate(CellMorphologyCreate):
    morphology_structure_type: Literal[MorphologyStructureType.COMPUTATIONAL]
    method: str
    score_dict: ScoreDict
    provenance: ScoreDict


class Placeholder(CellMorphologyRead):
    is_related_to: list[uuid.UUID]


class PlaceholderCreate(CellMorphologyCreate):
    morphology_structure_type: Literal[MorphologyStructureType.PLACEHOLDER]
    is_related_to: list[uuid.UUID]
