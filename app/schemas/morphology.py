from pydantic import BaseModel

from app.schemas.base import (
    BrainLocationCreate,
    BrainRegionRead,
    CreationMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    MeasurementCreate,
    MeasurementRead,
    SpeciesRead,
    StrainRead,
)


class ReconstructionMorphologyBase(BaseModel):
    name: str
    description: str
    brain_location: BrainLocationCreate | None

    class Config:
        from_attributes = True


class ReconstructionMorphologyCreate(ReconstructionMorphologyBase, LicensedCreateMixin):
    species_id: int
    strain_id: int
    brain_region_id: int
    legacy_id: str | None


class MorphologyFeatureAnnotationCreate(BaseModel):
    reconstruction_morphology_id: int
    measurements: list[MeasurementCreate]

    class Config:
        from_attributes = True


class MorphologyFeatureAnnotationRead(MorphologyFeatureAnnotationCreate, CreationMixin):
    measurements: list[MeasurementRead]


class ReconstructionMorphologyRead(
    ReconstructionMorphologyBase, CreationMixin, LicensedReadMixin
):
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead


class ReconstructionMorphologyExpand(ReconstructionMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationCreate | None
