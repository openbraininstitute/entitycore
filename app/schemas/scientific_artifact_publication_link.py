import uuid

from app.db.types import PublicationType
from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.publication import NestedPublicationRead
from app.schemas.scientific_artifact import NestedScientificArtifactRead


class ScientificArtifactPublicationLinkBase(Schema):
    publication_type: PublicationType


class ScientificArtifactPublicationLinkCreate(
    ScientificArtifactPublicationLinkBase, IdentifiableCreate
):
    publication_id: uuid.UUID
    scientific_artifact_id: uuid.UUID


class ScientificArtifactPublicationLinkRead(
    ScientificArtifactPublicationLinkBase,
    IdentifiableRead,
):
    publication: NestedPublicationRead
    scientific_artifact: NestedScientificArtifactRead
