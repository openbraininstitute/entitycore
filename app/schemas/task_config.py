import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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
from app.schemas.entity import NestedEntityCreate, NestedEntityRead
from app.schemas.utils import make_update_schema


class TaskConfigBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    task_config_type: TaskConfigType
    scan_parameters: JSON_DICT
    task_config_generator_id: uuid.UUID | None = None


class TaskConfigCreate(TaskConfigBase, AuthorizationOptionalPublicMixin):
    inputs: Annotated[
        list[NestedEntityCreate],
        Field(description="List of input entities (only ids)."),
    ] = []


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
    inputs: Annotated[
        list[NestedEntityRead],
        Field(description="List of input entities."),
    ] = []
