from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    MeasurementCreate,
    MeasurementRead,
    PointLocationBase,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributorRead
from app.schemas.mtype import MTypeClassRead


class ReconstructionMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None


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
    contributions: list[ContributorRead] | None
    mtypes: list[MTypeClassRead] | None


class ReconstructionMorphologyAnnotationExpandedRead(ReconstructionMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead
