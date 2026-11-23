from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.base import AuthorizedProjectIdMixin
from app.schemas.utils import make_update_schema


class SkeletonizationExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    pass


class SkeletonizationExecutionAdminCreate(AuthorizedProjectIdMixin, SkeletonizationExecutionCreate):
    pass


class SkeletonizationExecutionRead(ActivityRead, ExecutionActivityMixin):
    pass


class SkeletonizationExecutionUserUpdate(ActivityUpdate, ExecutionActivityMixin):
    pass


SkeletonizationExecutionAdminUpdate = make_update_schema(
    SkeletonizationExecutionCreate,
    "SkeletonizationExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
