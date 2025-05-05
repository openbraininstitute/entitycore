import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.db.types import PointLocationBase
from app.schemas.annotation import MTypeClassRead
from app.schemas.asset import AssetsMixin
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
from app.schemas.contribution import ContributionReadWithoutEntity


class ReconstructionMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None


class ReconstructionMorphologyCreate(
    ReconstructionMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID
    legacy_id: list[str] | None = None


class MorphologyFeatureAnnotationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reconstruction_morphology_id: uuid.UUID


class MorphologyFeatureAnnotationCreate(MorphologyFeatureAnnotationBase):
    measurements: Sequence[MeasurementCreate]


class MorphologyFeatureAnnotationRead(
    MorphologyFeatureAnnotationBase, CreationMixin, IdentifiableMixin
):
    measurements: Sequence[MeasurementRead]


class ReconstructionMorphologyRead(
    ReconstructionMorphologyBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    AssetsMixin,
):
    species: SpeciesRead
    strain: StrainRead | None
    brain_region: BrainRegionRead
    contributions: list[ContributionReadWithoutEntity] | None
    mtypes: list[MTypeClassRead] | None


class ReconstructionMorphologyAnnotationExpandedRead(ReconstructionMorphologyRead):
    morphology_feature_annotation: MorphologyFeatureAnnotationRead
