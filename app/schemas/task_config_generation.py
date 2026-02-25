from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class TaskConfigGenerationCreate(ActivityCreate):
    pass


class TaskConfigGenerationRead(ActivityRead):
    pass


class TaskConfigGenerationUserUpdate(ActivityUpdate):
    pass


TaskConfigGenerationAdminUpdate = make_update_schema(
    TaskConfigGenerationCreate,
    "TaskConfigGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
