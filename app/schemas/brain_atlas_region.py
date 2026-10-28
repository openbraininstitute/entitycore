import uuid

from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.utils import make_update_schema


class BrainAtlasRegionBaseMixin:
    volume: float | None
    is_leaf_region: bool

    brain_atlas_id: uuid.UUID
    brain_region_id: uuid.UUID


class BrainAtlasRegionCreate(
    BrainAtlasRegionBaseMixin,
    EntityCreate,
):
    pass


class BrainAtlasRegionRead(
    BrainAtlasRegionBaseMixin,
    EntityRead,
):
    pass


BrainAtlasRegionUpdate = make_update_schema(BrainAtlasRegionCreate, "BrainAtlasRegionUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasRegionAdminUpdate = make_update_schema(
    BrainAtlasRegionCreate,
    "BrainAtlasRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
