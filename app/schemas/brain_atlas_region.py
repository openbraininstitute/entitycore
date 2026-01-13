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
from app.schemas.brain_region import BrainRegionCreateMixin
from app.schemas.utils import make_update_schema


class BrainAtlasRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume: float | None
    is_leaf_region: bool

    brain_atlas_id: uuid.UUID
    brain_region_id: uuid.UUID


class BrainAtlasRegionCreate(
    BrainAtlasRegionBase,
    BrainRegionCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    pass


class BrainAtlasRegionRead(
    BrainAtlasRegionBase,
    AssetsMixin,
    AuthorizationMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    IdentifiableMixin,
):
    pass


BrainAtlasRegionUpdate = make_update_schema(BrainAtlasRegionCreate, "BrainAtlasRegionUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasRegionAdminUpdate = make_update_schema(
    BrainAtlasRegionCreate,
    "BrainAtlasRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
