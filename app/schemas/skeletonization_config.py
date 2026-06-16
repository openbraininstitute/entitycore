import uuid

from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class SkeletonizationConfigBaseMixin(NameDescriptionMixin):
    skeletonization_campaign_id: uuid.UUID
    em_cell_mesh_id: uuid.UUID
    scan_parameters: JSON_DICT


class SkeletonizationConfigCreate(SkeletonizationConfigBaseMixin, EntityCreate):
    pass


SkeletonizationConfigUserUpdate = make_update_schema(
    SkeletonizationConfigCreate, "SkeletonizationConfigUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

SkeletonizationConfigAdminUpdate = make_update_schema(
    SkeletonizationConfigCreate,
    "SkeletonizationConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSkeletonizationConfigRead(SkeletonizationConfigBaseMixin, NestedEntityRead):
    pass


class SkeletonizationConfigRead(
    SkeletonizationConfigBaseMixin,
    EntityRead,
):
    pass
