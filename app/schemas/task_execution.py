from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class TaskExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    pass


class TaskExecutionRead(ActivityRead, ExecutionActivityMixin):
    pass


class TaskExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    pass


TaskExecutionAdminUpdate = make_update_schema(
    TaskExecutionCreate,
    "TaskExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
