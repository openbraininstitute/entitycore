import uuid

from app.schemas.base import Schema, TimestapMixin


class PlatformUserBase(Schema):
    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class NestedPlatformUserRead(PlatformUserBase, TimestapMixin):
    id: uuid.UUID


class PlatformUserRead(PlatformUserBase, TimestapMixin):
    id: uuid.UUID
