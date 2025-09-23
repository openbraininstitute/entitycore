from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema


class IonChannelBase(BaseModel):
    """Base model for ion channel."""

    name: str
    description: str
    label: str
    gene: str
    synonyms: list[str]


class NestedIonChannelRead(
    IonChannelBase,
    IdentifiableMixin,
):
    """Nested read model for ion channel."""


class IonChannelRead(
    NestedIonChannelRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    """Read model for ion channel."""


class IonChannelCreate(IonChannelBase):
    """Create model for ion channel."""


IonChannelAdminUpdate = make_update_schema(
    IonChannelCreate,
    "IonChannelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
