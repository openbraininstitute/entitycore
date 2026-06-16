from __future__ import annotations

from pydantic import UUID4  # noqa: TC002

from app.schemas.base import Schema, TimestapMixin


class NestedIdentifiableRead(Schema, TimestapMixin):
    id: UUID4


class IdentifiableCreate(Schema):
    pass


class IdentifiableRead(NestedIdentifiableRead):
    created_by: NestedPersonRead
    updated_by: NestedPersonRead


from app.schemas.agent import NestedPersonRead  # noqa: E402, TC001

IdentifiableRead.model_rebuild()
