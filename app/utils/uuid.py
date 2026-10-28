import uuid
from typing import Any

import sqlalchemy as sa

from app.config import settings


def create_uuid() -> uuid.UUID:
    """Return a new random UUIDv4."""
    return uuid.uuid4()


def value_to_uuid(prefix: str, value: sa.SQLColumnExpression[Any]) -> sa.ColumnElement[uuid.UUID]:
    """Return a deterministic UUIDv5 SQL expression."""
    return sa.func.uuid_generate_v5(
        sa.literal(settings.UUID_NAMESPACE, type_=sa.UUID(as_uuid=True)),
        sa.literal(f"{prefix}/") + sa.cast(value, sa.Text),
        type_=sa.UUID(as_uuid=True),
    )
