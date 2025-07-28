import uuid

from pydantic import BaseModel

from app.db.types import STRING_LIST
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class IonChannelBase(BaseModel):
    """Base model for ion channel."""

    name: str
    description: str
    label: str
    gene: str
    synonyms: STRING_LIST


class IonChannelRead(
    IonChannelBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    """Read model for ion channel."""


class IonChannelCreate(IonChannelBase):
    """Create model for ion channel."""
