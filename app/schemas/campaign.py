from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT, TaskType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.entity import NestedEntityRead
from app.schemas.task_config import NestedTaskConfigRead
from app.schemas.utils import make_update_schema


class CampaignBase(
    BaseModel,
    NameDescriptionMixin,
):
    model_config = ConfigDict(from_attributes=True)
    task_type: TaskType
    scan_parameters: JSON_DICT


class CampaignCreate(
    CampaignBase,
    AuthorizationOptionalPublicMixin,
):
    pass


CampaignUserUpdate = make_update_schema(
    CampaignCreate,
    "CampaignUserUpdate",
)  # pyright: ignore [reportInvalidTypeForm]

CampaignAdminUpdate = make_update_schema(
    CampaignCreate,
    "CampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedCampaignRead(
    CampaignBase,
    EntityTypeMixin,
    IdentifiableMixin,
):
    pass


class CampaignRead(
    NestedCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    inputs: list[NestedEntityRead]
    configs: list[NestedTaskConfigRead]
