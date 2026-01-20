import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.types import ActivityStatus, ExecutorType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    ActivityTypeMixin,
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.entity import NestedEntityRead
from app.schemas.utils import NOT_SET, NotSet


class ActivityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ActivityStatus = ActivityStatus.done


class NestedActivityRead(ActivityBase, ActivityTypeMixin, IdentifiableMixin):
    pass


class ActivityRead(NestedActivityRead, CreatedByUpdatedByMixin, CreationMixin, AuthorizationMixin):
    used: list[NestedEntityRead]
    generated: list[NestedEntityRead]


class ActivityCreate(ActivityBase, AuthorizationOptionalPublicMixin):
    used_ids: list[uuid.UUID] = []
    generated_ids: list[uuid.UUID] = []


class ActivityUpdate(BaseModel):
    start_time: datetime | NotSet | None = NOT_SET
    end_time: datetime | NotSet | None = NOT_SET
    generated_ids: list[uuid.UUID] | NotSet | None = NOT_SET
    status: ActivityStatus | NotSet | None = NOT_SET


class ExecutionActivityMixin:
    executor: ExecutorType | None = None
    execution_id: uuid.UUID | None = None
