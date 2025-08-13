from pydantic import BaseModel

from app.db.types import ExternalSource
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class ExternalUrlBase(BaseModel):
    """Base model for external url."""

    external_source: ExternalSource
    url: str
    title: str | None = None


class ExternalUrlRead(ExternalUrlBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin):
    """Read model for external url."""


class ExternalUrlCreate(ExternalUrlBase):
    """Create model for external url."""
