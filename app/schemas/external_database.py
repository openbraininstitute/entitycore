import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class ExternalDatabaseBase(BaseModel):
    """Base model for external database."""

    label: str
    URL: str


class ExternalDatabaseRead(
    ExternalDatabaseBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for external database."""


class ExternalDatabaseCreate(ExternalDatabaseBase):
    """Create model for external database."""


class ExternalDatabaseURLBase(BaseModel):
    """Base model for external database URL."""

    external_database_id: uuid.UUID
    URL: str


class ExternalDatabaseURLRead(
    ExternalDatabaseURLBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for external database URL."""


class ExternalDatabaseURLCreate(ExternalDatabaseURLBase):
    """Create model for external database URL."""
