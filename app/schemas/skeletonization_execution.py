from app.db.types import SkeletonizationExecutionStatus
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class SkeletonizationExecutionCreate(ActivityCreate):
    status: SkeletonizationExecutionStatus


class SkeletonizationExecutionRead(ActivityRead):
    status: SkeletonizationExecutionStatus


class SkeletonizationExecutionUserUpdate(ActivityUpdate):
    status: SkeletonizationExecutionStatus | None = None


SkeletonizationExecutionAdminUpdate = make_update_schema(
    SkeletonizationExecutionCreate,
    "SkeletonizationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
