import uuid

from pydantic import BaseModel

from app.db.types import ValidationType
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)


class ValidationCreate(ActivityCreate):
    validation_type: ValidationType


class ValidationRead(ActivityRead):
    validation_type: ValidationType


class ValidationUpdate(ActivityUpdate):
    validation_type: ValidationType | None = None


class ValidationResultBase(BaseModel):
    name: str
    passed: bool
    validated_entity_id: uuid.UUID


class ValidationResultRead(
    ValidationResultBase,
    CreationMixin,
    IdentifiableMixin,
    CreatedByUpdatedByMixin,
    AuthorizationMixin,
):
    pass


class ValidationResultCreate(ValidationResultBase, AuthorizationOptionalPublicMixin):
    pass
