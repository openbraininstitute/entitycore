import uuid
from typing import Annotated, Any

from pydantic import Field

from app.db.types import TaskConfigType
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityCreate, NestedEntityRead
from app.schemas.utils import make_update_schema


class TaskConfigBaseMixin(NameDescriptionMixin):
    task_config_type: TaskConfigType
    meta: dict[str, Any]
    task_config_generator_id: uuid.UUID | None = None


class TaskConfigCreate(EntityCreate, TaskConfigBaseMixin):
    inputs: Annotated[
        list[NestedEntityCreate],
        Field(description="List of input entities (only ids)."),
    ] = []  # ruff:ignore[mutable-class-default]


TaskConfigUserUpdate = make_update_schema(
    TaskConfigCreate,
    "TaskConfigUserUpdate",
)  # pyright: ignore [reportInvalidTypeForm]

TaskConfigAdminUpdate = make_update_schema(
    TaskConfigCreate,
    "TaskConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedTaskConfigRead(NestedEntityRead, TaskConfigBaseMixin):
    pass


class TaskConfigRead(
    EntityRead,
    TaskConfigBaseMixin,
):
    inputs: Annotated[
        list[NestedEntityRead],
        Field(description="List of input entities."),
    ] = []  # ruff:ignore[mutable-class-default]
