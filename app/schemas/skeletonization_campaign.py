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
from app.schemas.em_cell_mesh import NestedEMCellMeshRead
from app.schemas.skeletonization_config import NestedSkeletonizationConfigRead
from app.schemas.utils import make_update_schema


class SkeletonizationCampaignBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT


class SkeletonizationCampaignCreate(SkeletonizationCampaignBase, AuthorizationOptionalPublicMixin):
    pass


SkeletonizationCampaignUserUpdate = make_update_schema(
    SkeletonizationCampaignCreate, "SkeletonizationCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
SkeletonizationCampaignAdminUpdate = make_update_schema(
    SkeletonizationCampaignCreate,
    "SkeletonizationCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSkeletonizationCampaignRead(
    SkeletonizationCampaignBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class SkeletonizationCampaignRead(
    NestedSkeletonizationCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    input_meshes: list[NestedEMCellMeshRead]
    skeletonization_configs: list[NestedSkeletonizationConfigRead]
