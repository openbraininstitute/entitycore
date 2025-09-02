import uuid

from pydantic import BaseModel

from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)


class ValidationCreate(ActivityCreate):
    pass


class ValidationRead(ActivityRead):
    pass


class ValidationUpdate(ActivityUpdate):
    pass


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
    AssetsMixin,
):
    pass


class ValidationResultCreate(ValidationResultBase, AuthorizationOptionalPublicMixin):
    pass
