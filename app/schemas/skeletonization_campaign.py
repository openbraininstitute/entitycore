from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.em_cell_mesh import NestedEMCellMeshRead
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityCreate, NestedEntityRead
from app.schemas.skeletonization_config import NestedSkeletonizationConfigRead
from app.schemas.utils import make_update_schema


class SkeletonizationCampaignBaseMixin(NameDescriptionMixin):
    scan_parameters: JSON_DICT


class SkeletonizationCampaignCreate(
    SkeletonizationCampaignBaseMixin,
    EntityCreate,
):
    input_meshes: list[NestedEntityCreate] = []  # noqa: RUF012


SkeletonizationCampaignUserUpdate = make_update_schema(
    SkeletonizationCampaignCreate, "SkeletonizationCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
SkeletonizationCampaignAdminUpdate = make_update_schema(
    SkeletonizationCampaignCreate,
    "SkeletonizationCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSkeletonizationCampaignRead(
    SkeletonizationCampaignBaseMixin,
    NestedEntityRead,
):
    pass


class SkeletonizationCampaignRead(
    SkeletonizationCampaignBaseMixin,
    EntityRead,
):
    input_meshes: list[NestedEMCellMeshRead]
    skeletonization_configs: list[NestedSkeletonizationConfigRead]
