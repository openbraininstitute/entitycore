import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.db.model import CircuitBuildCategory, CircuitScale
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    SpeciesRead,
    StrainRead,
)
from app.schemas.contribution import ContributionReadWithoutEntity


class CircuitBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str | None


class CircuitCreate(CircuitBase, AuthorizationOptionalPublicMixin, LicensedCreateMixin):
    subject_id: uuid.UUID
    species_id: uuid.UUID
    brain_region_id: uuid.UUID
    experiment_date: datetime | None
    published_in : dict | None
    contact_id : uuid.UUID | None

    parent_circuit_id: uuid.UUID | None
    atlas_id: uuid.UUID | None
    build_category: CircuitBuildCategory
    scale: CircuitScale
    has_morphologies: bool
    has_point_neurons: bool
    has_electrical_cell_models: bool
    has_spines: bool
    is_simulatable: bool
    version: str | None


class CircuitRead(
    CircuitBase,
    BrainRegionReadMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    CreationMixin,
    EntityTypeMixin,
    AssetsMixin,
    SubjectRead,
    ContributionReadWithoutEntityMixin,
):
    id: uuid.UUID

    # TODO...
