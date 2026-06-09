# app/schemas/task_result.py

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.types import TaskResultType
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
from app.schemas.utils import make_update_schema


class TaskResultBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)


class TaskResultCreate(TaskResultBase, AuthorizationOptionalPublicMixin):
    data_payload: dict[str, Any] = {}
    result_type: TaskResultType = TaskResultType.task_result


TaskResultUserUpdate = make_update_schema(TaskResultCreate, "TaskResultUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
TaskResultAdminUpdate = make_update_schema(
    TaskResultCreate,
    "TaskResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedTaskResultRead(TaskResultBase, EntityTypeMixin, IdentifiableMixin):
    pass


class TaskResultRead(
    NestedTaskResultRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    result_type: TaskResultType
    data_payload: dict[str, Any]
