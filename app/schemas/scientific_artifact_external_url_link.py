import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import IdentifiableMixin
from app.schemas.external_url import NestedExternalUrlRead
from app.schemas.scientific_artifact import NestedScientificArtifactRead


class ScientificArtifactExternalUrlLinkBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScientificArtifactExternalUrlLinkCreate(ScientificArtifactExternalUrlLinkBase):
    external_url_id: uuid.UUID
    scientific_artifact_id: uuid.UUID


class ScientificArtifactExternalUrlLinkRead(
    ScientificArtifactExternalUrlLinkBase,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
):
    external_url: NestedExternalUrlRead
    scientific_artifact: NestedScientificArtifactRead
