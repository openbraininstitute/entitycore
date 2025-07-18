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
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin


class ScientificArtifactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experiment_date: datetime | None = None
    contact_email: str | None = None
    atlas_id: uuid.UUID | None = None


class ScientificArtifactRead(
    ScientificArtifactBase,
    SubjectReadMixin,
    BrainRegionReadMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    LicenseReadMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    AuthorizationMixin,
    AssetsMixin,
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
