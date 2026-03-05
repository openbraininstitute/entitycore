from app.db.types import TaskActivityType
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class TaskActivityBase(ExecutionActivityMixin):
    task_activity_type: TaskActivityType | None = None


class TaskActivityCreate(ActivityCreate, TaskActivityBase):
    pass


class TaskActivityRead(ActivityRead, TaskActivityBase):
    pass


class TaskActivityUserUpdate(ActivityUpdate, TaskActivityBase):
    pass


TaskActivityAdminUpdate = make_update_schema(
    TaskActivityCreate,
    "TaskActivityAdminUpdate",
    excluded_fields={"task_activity_type"},
)  # pyright : ignore [reportInvalidTypeForm]
