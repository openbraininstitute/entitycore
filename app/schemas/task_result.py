# app/schemas/task_result.py

from typing import Any

from app.db.types import TaskResultType
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class TaskResultBaseMixin(NameDescriptionMixin):
    pass


class TaskResultCreate(TaskResultBaseMixin, EntityCreate):
    data_payload: dict[str, Any] = {}  # ruff:ignore[mutable-class-default]
    task_result_type: TaskResultType = TaskResultType.circuit_extraction__circuit


TaskResultUserUpdate = make_update_schema(TaskResultCreate, "TaskResultUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
TaskResultAdminUpdate = make_update_schema(
    TaskResultCreate,
    "TaskResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedTaskResultRead(TaskResultBaseMixin, NestedEntityRead):
    pass


class TaskResultRead(TaskResultBaseMixin, EntityRead):
    task_result_type: TaskResultType
    data_payload: dict[str, Any]
