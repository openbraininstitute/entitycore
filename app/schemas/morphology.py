import uuid
from enum import Enum, auto
from pydantic import BaseModel, ConfigDict
from typing import Literal

from app.db.types import PointLocationBase, MorphologyStructureType
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


class ExperimentalMorphologyMethod(BaseModel):
    """Experimental morphology method for capturing cell morphology data.

    Parameters:
    -----------
    protocol_design: str
        From a controlled vocabulary (e.g., EM, CellPatch, Fluorophore, Imp)
    protocol_document: str, optional
        URL link to protocol document or publication
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
    protocol_document: str | None = None
    slicing_direction: str | None = None
    magnification: float | None = None
    tissue_shrinkage: float | None = None
    has_been_corrected_for_shrinkage: bool | None = None

    class Config:
        from_attributes = True


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    legacy_id: list[str] | None = None


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
    structure_type: MorphologyStructureType


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None


class ScoreDict(BaseModel):
    x: dict[str, float]


class PipelineType(str, Enum):
    Raw = "Raw"
    Curated = "Curated"
    Unraveled = "Unraveled"
    Repaired = "Repaired"


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
    structure_type: Literal[MorphologyStructureType.digital_reconstruction]
    reconstruction_method: ExperimentalMorphologyMethod
    pipeline_state: PipelineType
    is_related_to: list[uuid.UUID]


class ModifiedReconstruction(CellMorphologyRead):
    method: MethodsType
    is_related_to: list[uuid.UUID]


class ModifiedReconstructionCreate(CellMorphologyCreate):
    structure_type: Literal[MorphologyStructureType.modified]
    method: MethodsType
    is_related_to: list[uuid.UUID]


class ComputationallySynthesized(CellMorphologyRead):
    method: str
    score_dict: ScoreDict
    provenance: ScoreDict


class ComputationallySynthesizedCreate(CellMorphologyCreate):
    structure_type: Literal[MorphologyStructureType.computationally_synthesized]
    method: str
    score_dict: ScoreDict
    provenance: ScoreDict


class Placeholder(CellMorphologyRead):
    is_related_to: list[uuid.UUID]


class PlaceholderCreate(CellMorphologyCreate):
    structure_type: Literal[MorphologyStructureType.placeholder]
    is_related_to: list[uuid.UUID]
