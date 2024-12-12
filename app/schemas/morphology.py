from pydantic import BaseModel
from typing import List, Optional
from app.schemas.base import (
    CreationMixin,
    LicensedReadMixin,
    LicensedCreateMixin,
    BrainLocationCreate,
    BrainRegionRead,
    MeasurementCreate,
    MeasurementRead,
    SpeciesRead,
    StrainRead,
)


class ReconstructionMorphologyBase(BaseModel):
    name: str
    description: str
    brain_location: Optional[BrainLocationCreate]

    class Config:
        from_attributes = True


class ReconstructionMorphologyCreate(ReconstructionMorphologyBase, LicensedCreateMixin):
    species_id: int
    strain_id: int
    brain_region_id: int
    legacy_id: Optional[str]


class MorphologyFeatureAnnotationCreate(BaseModel):
    reconstruction_morphology_id: int
    measurements: List[MeasurementCreate]

    class Config:
        from_attributes = True


class MorphologyFeatureAnnotationRead(MorphologyFeatureAnnotationCreate, CreationMixin):
    measurements: List[MeasurementRead]


class ReconstructionMorphologyRead(
    ReconstructionMorphologyBase, CreationMixin, LicensedReadMixin
):
    species: SpeciesRead
    strain: Optional[StrainRead]
    brain_region: BrainRegionRead


class ReconstructionMorphologyExpand(ReconstructionMorphologyRead):
    morphology_feature_annotation: Optional[MorphologyFeatureAnnotationCreate]
