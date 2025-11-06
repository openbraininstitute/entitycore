from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.utils import make_update_schema


class SkeletonizationConfigBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT


class SkeletonizationConfigCreate(SkeletonizationConfigBase, AuthorizationOptionalPublicMixin):
    pass


SkeletonizationConfigUserUpdate = make_update_schema(
    SkeletonizationConfigCreate, "SkeletonizationConfigUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

SkeletonizationConfigAdminUpdate = make_update_schema(
    SkeletonizationConfigCreate,
    "SkeletonizationConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSkeletonizationConfigRead(
    SkeletonizationConfigBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class SkeletonizationConfigRead(
    NestedSkeletonizationConfigRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    pass
