import uuid

from app.schemas.base import Schema
from app.schemas.external_url import NestedExternalUrlRead
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.scientific_artifact import NestedScientificArtifactRead


class ScientificArtifactExternalUrlLinkBase(Schema):
    pass


class ScientificArtifactExternalUrlLinkCreate(
    ScientificArtifactExternalUrlLinkBase, IdentifiableCreate
):
    external_url_id: uuid.UUID
    scientific_artifact_id: uuid.UUID


class ScientificArtifactExternalUrlLinkRead(
    ScientificArtifactExternalUrlLinkBase,
    IdentifiableRead,
):
    external_url: NestedExternalUrlRead
    scientific_artifact: NestedScientificArtifactRead
