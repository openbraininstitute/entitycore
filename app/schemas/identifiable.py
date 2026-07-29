from uuid import UUID

from app.schemas.base import Schema, TimestapMixin
from app.schemas.user import NestedUserRead


class NestedIdentifiableRead(Schema, TimestapMixin):
    id: UUID


class IdentifiableCreate(Schema):
    pass


class IdentifiableRead(NestedIdentifiableRead):
    created_by: NestedUserRead
    updated_by: NestedUserRead
