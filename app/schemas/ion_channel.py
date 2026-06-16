from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class IonChannelBaseMixin(NameDescriptionMixin):
    """Base model for ion channel."""

    label: str
    gene: str
    synonyms: list[str]


class NestedIonChannelRead(
    IonChannelBaseMixin,
    NestedIdentifiableRead,
):
    """Nested read model for ion channel."""


class IonChannelRead(
    IonChannelBaseMixin,
    IdentifiableRead,
):
    """Read model for ion channel."""


class IonChannelCreate(IonChannelBaseMixin, IdentifiableCreate):
    """Create model for ion channel."""


IonChannelAdminUpdate = make_update_schema(
    IonChannelCreate,
    "IonChannelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
