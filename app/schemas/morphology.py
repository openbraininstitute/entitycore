import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict
from typing import Dict, List
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

class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 #   name: str
 #   description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None
    mtype_dict: Dict[str, str] = {}  # Added dictionary for ClassificationScheme: mtype 
    etype_dict: Dict[str, str] = {}  # Added dictionary for ClassificationScheme: etype 
    ttype_dict: Dict[str, str] = {}  # Added dictionary for ClassificationScheme: ttype 

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
    pipeline_state: PipelineType
    is_related_to: List[uuid.UUID]

class DigitalReconstructionCreate(CellMorphologyCreate):
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
