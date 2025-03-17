import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

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
    PointLocationBase,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity
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
    species_id: uuid.UUID
    strain_id: uuid.UUID | None
    brain_region_id: int
    legacy_id: str | None


class MorphologyFeatureAnnotationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reconstruction_morphology_id: uuid.UUID
    measurements: Sequence[MeasurementCreate]


class MorphologyFeatureAnnotationRead(
    MorphologyFeatureAnnotationCreate, CreationMixin, IdentifiableMixin
):
    measurements: Sequence[MeasurementRead]


class ReconstructionMorphologyRead(
    ReconstructionMorphologyBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
):
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None


class ReconstructionMorphologyAnnotationExpandedRead(ReconstructionMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead
