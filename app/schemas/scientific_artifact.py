import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    BrainRegionCreateMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    LicenseCreateMixin,
    LicenseReadMixin,
    IdentifiableMixin,
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
)
from app.schemas.subject import SubjectCreateMixin, SubjectReadMixin


class ScientificArtifactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experiment_date: datetime | None = None
    contact_id: uuid.UUID | None = None
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
