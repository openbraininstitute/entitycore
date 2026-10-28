from uuid import UUID

from app.schemas.base import Schema, TimestapMixin
from app.schemas.platform_user import NestedPlatformUserRead


class NestedIdentifiableRead(Schema, TimestapMixin):
    id: UUID


class IdentifiableCreate(Schema):
    pass


class IdentifiableRead(NestedIdentifiableRead):
    created_by: NestedPlatformUserRead
    updated_by: NestedPlatformUserRead
