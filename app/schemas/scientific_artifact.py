import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicenseCreateMixin,
    LicenseReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin


class ScientificArtifactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experiment_date: datetime | None = None
    contact_email: str | None = None
    published_in: str | None = None
    atlas_id: uuid.UUID | None = None


class NestedScientificArtifactRead(
    ScientificArtifactBase,
    IdentifiableMixin,
    EntityTypeMixin,
    AuthorizationMixin,
):
    pass


class ScientificArtifactRead(
    NestedScientificArtifactRead,
    SubjectReadMixin,
    BrainRegionReadMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    LicenseReadMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
):
    pass


class ScientificArtifactCreate(
    ScientificArtifactBase,
    SubjectCreateMixin,
    BrainRegionCreateMixin,
    LicenseCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    pass
