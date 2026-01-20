from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class IonChannelModelingExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    pass


class IonChannelModelingExecutionRead(ActivityRead, ExecutionActivityMixin):
    pass


class IonChannelModelingExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    pass


IonChannelModelingExecutionAdminUpdate = make_update_schema(
    IonChannelModelingExecutionCreate,
    "IonChannelModelingExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
