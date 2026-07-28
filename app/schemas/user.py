import uuid

from app.schemas.base import Schema, TimestapMixin
from app.schemas.utils import make_update_schema


class UserBase(Schema):
    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class NestedUserRead(UserBase, TimestapMixin):
    id: uuid.UUID


class UserRead(UserBase, TimestapMixin):
    id: uuid.UUID


UserAdminUpdate = make_update_schema(
    UserBase,
    "UserAdminUpdate",
    excluded_fields=set(),
)  # pyright: ignore [reportInvalidTypeForm]
