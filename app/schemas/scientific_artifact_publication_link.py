import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import PublicationType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    IdentifiableMixin,
)
from app.schemas.publication import NestedPublicationRead
from app.schemas.scientific_artifact import NestedScientificArtifactRead


class ScientificArtifactPublicationLinkBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    publication_type: PublicationType


class ScientificArtifactPublicationLinkCreate(ScientificArtifactPublicationLinkBase):
    publication_id: uuid.UUID
    scientific_artifact_id: uuid.UUID


class ScientificArtifactPublicationLinkRead(
    ScientificArtifactPublicationLinkBase,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
):
    publication: NestedPublicationRead
    scientific_artifact: NestedScientificArtifactRead
