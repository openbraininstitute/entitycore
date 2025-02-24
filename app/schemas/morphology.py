from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
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
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    brain_location: BrainLocationCreate | None


class ReconstructionMorphologyCreate(
    ReconstructionMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: int
    strain_id: int | None
    brain_region_id: int
    legacy_id: str | None


class MorphologyFeatureAnnotationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reconstruction_morphology_id: int
    measurements: Sequence[MeasurementCreate]


class MorphologyFeatureAnnotationRead(MorphologyFeatureAnnotationCreate, CreationMixin):
    measurements: Sequence[MeasurementRead]


class ReconstructionMorphologyRead(
    ReconstructionMorphologyBase,
    CreationMixin,
    LicensedReadMixin,
    AuthorizationMixin,
):
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead


class ReconstructionMorphologyExpand(ReconstructionMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationCreate | None
