from app.db.types import IonChannelModelingExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class IonChannelModelingExecutionCreate(ActivityCreate):
    status: IonChannelModelingExecutionStatus


class IonChannelModelingExecutionRead(ActivityRead):
    status: IonChannelModelingExecutionStatus


class IonChannelModelingExecutionUserUpdate(ActivityUpdate):
    status: IonChannelModelingExecutionStatus | None = None


IonChannelModelingExecutionAdminUpdate = make_update_schema(
    IonChannelModelingExecutionCreate,
    "IonChannelModelingExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
