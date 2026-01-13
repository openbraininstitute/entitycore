import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.species import NestedSpeciesRead


class BrainAtlasBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    hierarchy_id: uuid.UUID
    species: NestedSpeciesRead


class BrainAtlasCreate(
    BrainAtlasBase,
    AuthorizationOptionalPublicMixin,
):
    pass


class BrainAtlasRead(
    AuthorizationMixin,
    BrainAtlasBase,
    CreationMixin,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
    AssetsMixin,
):
    pass
