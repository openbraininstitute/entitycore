import uuid
from datetime import datetime

from app.db.types import ActivityStatus, ExecutorType
from app.schemas.base import (
    ActivityTypeMixin,
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    Schema,
)
from app.schemas.entity import NestedEntityRead
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead


class ActivityBase(Schema):
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ActivityStatus = ActivityStatus.done


class NestedActivityRead(ActivityBase, ActivityTypeMixin, NestedIdentifiableRead):
    pass


class ActivityRead(ActivityBase, ActivityTypeMixin, AuthorizationMixin, IdentifiableRead):
    used: list[NestedEntityRead]
    generated: list[NestedEntityRead]


class ActivityCreate(ActivityBase, IdentifiableCreate, AuthorizationOptionalPublicMixin):
    used_ids: list[uuid.UUID] = []  # ruff:ignore[mutable-class-default]
    generated_ids: list[uuid.UUID] = []  # ruff:ignore[mutable-class-default]


class ActivityUpdate(Schema):
    start_time: datetime | None = None
    end_time: datetime | None = None
    generated_ids: list[uuid.UUID] | None = None
    status: ActivityStatus | None = None


class ExecutionActivityMixin:
    executor: ExecutorType | None = None
    execution_id: uuid.UUID | None = None
