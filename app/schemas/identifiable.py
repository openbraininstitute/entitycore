from __future__ import annotations

from uuid import UUID  # ruff:ignore[typing-only-standard-library-import]

from app.schemas.base import Schema, TimestapMixin


class NestedIdentifiableRead(Schema, TimestapMixin):
    id: UUID


class IdentifiableCreate(Schema):
    pass


class IdentifiableRead(NestedIdentifiableRead):
    created_by: NestedUserRead
    updated_by: NestedUserRead


from app.schemas.user import (  # ruff:ignore[module-import-not-at-top-of-file]
    NestedUserRead,  # ruff:ignore[typing-only-first-party-import]
)

IdentifiableRead.model_rebuild()
