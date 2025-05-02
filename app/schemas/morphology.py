import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.db.types import PointLocationBase
from app.schemas.annotation import MTypeClassRead
from app.schemas.asset import AssetRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    MeasurementCreate,
    MeasurementRead,
    SpeciesRead,
    StrainRead,
)

from app.schemas.scientific_artifact import (
    ScientificArtifactMixin,
)

from app.schemas.contribution import ContributionReadWithoutEntity

class ExperimentalMorphologyMethod(BaseModel):
    def __init__(
        self,
        protocol_design: str,
        staining_method: str,
        slicing_thickness: float,
        protocol_document: str = None,
        slicing_direction: str = None,  # Changed from float to str
        magnification: float = None,
        tissue_shrinkage: float = None,
        has_been_corrected_for_shrinkage: bool = None
    ):
        """
        Experimental morphology method for capturing cell morphology data.
        
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
        self.protocol_design = protocol_design
        self.protocol_document = protocol_document
        self.staining_method = staining_method
        self.slicing_thickness = slicing_thickness
        self.slicing_direction = slicing_direction
        self.magnification = magnification
        self.tissue_shrinkage = tissue_shrinkage
        self.has_been_corrected_for_shrinkage = has_been_corrected_for_shrinkage


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location: PointLocationBase | None
    legacy_id: list[str] | None


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
    ScientificArtifactMixin,  # Added ScientificArtifactMixin
):
  #  species_id: uuid.UUID
  #  strain_id: uuid.UUID | None = None
  #  brain_region_id: int
    legacy_id: list[str] | None = None


class CellMorphologyRead(
    CellMorphologyBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    ScientificArtifactMixin,
):
   # species: SpeciesRead
   # strain: StrainRead | None
   # brain_region: BrainRegionRead
   # contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None
    assets: list[AssetRead] | None



from enum import Enum, auto

from typing import Dict
from pydantic import BaseModel, ValidationError
class ScoreDict(BaseModel):
    x: Dict[str, float]

class PipelineType(Enum):
    Raw = auto() 
    Curated  = auto() 
    Unraveled  = auto() 
    Repaired = auto()  

from typing import List

class MethodsType(Enum):
    Cloned = auto() 
    Mix_and_match  = auto() 
    Mousified  = auto() 
    Ratified = auto() 

class DigitalReconstruction(CellMorphologyBase):
    method: ExperimentalMorphologyMethod
    pipeline_state: PipelineType
    is_related_to: List[uuid.UUID]

class DigitalReconstructionCreate(CellMorphologyCreate):
    method: ExperimentalMorphologyMethod   
    pipeline_state: PipelineType
    is_related_to: List[uuid.UUID]

class ModifiedReconstruction(CellMorphologyBase):
    method: MethodsType
    is_related_to:List[uuid.UUID]

class ModifiedReconstructionCreate(CellMorphologyCreate):
    method: MethodsType
    is_related_to:List[uuid.UUID]

class ComputationallySynthesized(CellMorphologyBase):
    method: str
    score_dict: ScoreDict
    provenance: ScoreDict

class ComputationallySynthesizedCreate(CellMorphologyCreate):
    method: str
    score_dict: ScoreDict
    provenance: ScoreDict

class Placeholder(CellMorphologyBase):
    is_related_to:List[uuid.UUID]

class PlaceholderCreate(CellMorphologyCreate):
    is_related_to:List[uuid.UUID]

class MorphologyFeatureAnnotationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cell_morphology_id: uuid.UUID

class MorphologyFeatureAnnotationCreate(MorphologyFeatureAnnotationBase):
    measurements: Sequence[MeasurementCreate]

class MorphologyFeatureAnnotationRead(
    MorphologyFeatureAnnotationBase, CreationMixin, IdentifiableMixin
):
    measurements: Sequence[MeasurementRead]

# First, define the base annotation expanded class
class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead

# Then create specific subclasses for each morphology type
class DigitalReconstructionAnnotationExpandedRead(DigitalReconstruction):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead

class ModifiedReconstructionAnnotationExpandedRead(ModifiedReconstruction):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead

class ComputationallySynthesizedAnnotationExpandedRead(ComputationallySynthesized):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead

class PlaceholderAnnotationExpandedRead(Placeholder):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead