from app.db.types import IonChannelModelingExecutionStatus
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class IonChannelModelingExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    status: IonChannelModelingExecutionStatus


class IonChannelModelingExecutionRead(ActivityRead, ExecutionActivityMixin):
    status: IonChannelModelingExecutionStatus


class IonChannelModelingExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    status: IonChannelModelingExecutionStatus | None = None


IonChannelModelingExecutionAdminUpdate = make_update_schema(
    IonChannelModelingExecutionCreate,
    "IonChannelModelingExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
