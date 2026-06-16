import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.utils import make_update_schema


class BrainAtlasRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume: float | None
    is_leaf_region: bool

    brain_atlas_id: uuid.UUID
    brain_region_id: uuid.UUID


class BrainAtlasRegionCreate(
    BrainAtlasRegionBase,
    EntityCreate,
):
    pass


class BrainAtlasRegionRead(
    BrainAtlasRegionBase,
    EntityRead,
):
    pass


BrainAtlasRegionUpdate = make_update_schema(BrainAtlasRegionCreate, "BrainAtlasRegionUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasRegionAdminUpdate = make_update_schema(
    BrainAtlasRegionCreate,
    "BrainAtlasRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
