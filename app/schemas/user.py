import uuid

from app.schemas.base import Schema, TimestapMixin


class UserBase(Schema):
    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class NestedUserRead(UserBase, TimestapMixin):
    id: uuid.UUID


class UserRead(UserBase, TimestapMixin):
    id: uuid.UUID
