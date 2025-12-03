from app.db.types import SkeletonizationExecutionStatus
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.utils import make_update_schema


class SkeletonizationExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    status: SkeletonizationExecutionStatus


class SkeletonizationExecutionRead(ActivityRead, ExecutionActivityMixin):
    status: SkeletonizationExecutionStatus


class SkeletonizationExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    status: SkeletonizationExecutionStatus | None = None


SkeletonizationExecutionAdminUpdate = make_update_schema(
    SkeletonizationExecutionCreate,
    "SkeletonizationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
