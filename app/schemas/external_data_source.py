import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class ExternalDataSourceBase(BaseModel):
    """Base model for external data source."""

    label: str
    URL: str


class ExternalDataSourceRead(
    ExternalDataSourceBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for external data source."""


class ExternalDataSourceCreate(ExternalDataSourceBase):
    """Create model for external data source."""


class ExternalDataSourcePageBase(BaseModel):
    """Base model for external data source page."""

    external_data_source_id: uuid.UUID
    URL: str


class ExternalDataSourcePageRead(
    ExternalDataSourcePageBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for external data source page."""


class ExternalDataSourcePageCreate(ExternalDataSourcePageBase):
    """Create model for external data source page."""
