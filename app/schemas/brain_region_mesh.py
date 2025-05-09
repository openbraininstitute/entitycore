import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)


class BrainRegionMeshBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str


class BrainRegionMeshCreate(BrainRegionMeshBase, AuthorizationOptionalPublicMixin):
    brain_region_id: uuid.UUID


class BrainRegionMeshRead(
    BrainRegionMeshBase, CreationMixin, IdentifiableMixin, AuthorizationMixin, EntityTypeMixin
):
    brain_region: BrainRegionRead
