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
from app.schemas.utils import make_update_schema


class ValidationCreate(ActivityCreate):
    pass


class ValidationRead(ActivityRead):
    pass


class ValidationUserUpdate(ActivityUpdate):
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


ValidationResultUserUpdate = make_update_schema(
    ValidationResultCreate, "ValidationResultUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ValidationResultAdminUpdate = make_update_schema(
    ValidationResultCreate,
    "ValidationResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ValidationAdminUpdate = make_update_schema(
    ValidationCreate,
    "ValidationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
