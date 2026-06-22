from __future__ import annotations

from uuid import UUID  # noqa: TC003

from app.schemas.base import Schema, TimestapMixin


class NestedIdentifiableRead(Schema, TimestapMixin):
    id: UUID


class IdentifiableCreate(Schema):
    pass


class IdentifiableRead(NestedIdentifiableRead):
    created_by: NestedPersonRead
    updated_by: NestedPersonRead


from app.schemas.agent import NestedPersonRead  # noqa: E402, TC001

IdentifiableRead.model_rebuild()
