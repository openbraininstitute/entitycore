import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    ActivityTypeMixin,
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.entity import NestedEntityRead


class ActivityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime | None = None
    end_time: datetime | None = None


class NestedActivityRead(ActivityBase, ActivityTypeMixin, IdentifiableMixin):
    pass


class ActivityRead(NestedActivityRead, CreatedByUpdatedByMixin, CreationMixin, AuthorizationMixin):
    used: list[NestedEntityRead]
    generated: list[NestedEntityRead]


class ActivityCreate(ActivityBase, AuthorizationOptionalPublicMixin):
    used_ids: list[uuid.UUID] = []
    generated_ids: list[uuid.UUID] = []


class ActivityUpdate(ActivityBase, AuthorizationOptionalPublicMixin):
    end_time: datetime | None = None
    generated_ids: list[uuid.UUID] | None = None
