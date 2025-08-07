from pydantic import BaseModel

from app.db.types import ExternalDataSource
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class ExternalDataSourcePageBase(BaseModel):
    """Base model for external data source page."""

    source_label: ExternalDataSource
    url: str


class ExternalDataSourcePageRead(
    ExternalDataSourcePageBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for external data source page."""


class ExternalDataSourcePageCreate(ExternalDataSourcePageBase):
    """Create model for external data source page."""
