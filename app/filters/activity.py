import uuid
from datetime import datetime

from app.db.types import ActivityStatus, ExecutorType
from app.filters.common import (
    AuthorizedFilterMixin,
    CreationFilterMixin,
    IdFilterMixin,
)
from app.filters.entity import NestedEntityFilter
from app.filters.platform_user import CreatorFilterMixin


class ActivityFilterMixin(
    IdFilterMixin,
    AuthorizedFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
):
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ActivityStatus | None = None

    used: NestedEntityFilter | None = None
    generated: NestedEntityFilter | None = None


class ExecutionActivityFilterMixin:
    executor: ExecutorType | None = None
    execution_id: uuid.UUID | None = None
