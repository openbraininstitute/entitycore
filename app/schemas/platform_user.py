import uuid

from app.schemas.base import Schema, TimestapMixin


class PlatformUserBase(Schema):
    pref_label: str


class NestedPlatformUserRead(PlatformUserBase, TimestapMixin):
    id: uuid.UUID


class PlatformUserRead(PlatformUserBase, TimestapMixin):
    id: uuid.UUID
