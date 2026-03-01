import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT, TaskConfigType
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
from app.schemas.utils import make_update_schema


class TaskConfigBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    task_config_type: TaskConfigType
    scan_parameters: JSON_DICT
    parent_id: uuid.UUID | None = None


class TaskConfigCreate(TaskConfigBase, AuthorizationOptionalPublicMixin):
    input_ids: list[uuid.UUID] = []


TaskConfigUserUpdate = make_update_schema(
    TaskConfigCreate,
    "TaskConfigUserUpdate",
)  # pyright: ignore [reportInvalidTypeForm]

TaskConfigAdminUpdate = make_update_schema(
    TaskConfigCreate,
    "TaskConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedTaskConfigRead(TaskConfigBase, EntityTypeMixin, IdentifiableMixin):
    pass


class TaskConfigRead(
    NestedTaskConfigRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    input: list[NestedEntityRead]
