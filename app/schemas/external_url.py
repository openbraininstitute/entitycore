from pydantic import (
    computed_field,
    model_validator,
)

from app.db.types import EXTERNAL_SOURCE_INFO, ExternalSource
from app.schemas.base import NameDescriptionMixin
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.types import SerializableHttpUrl
from app.schemas.utils import make_update_schema


class ExternalUrlBaseMixin(NameDescriptionMixin):
    """Base model for external url."""

    source: ExternalSource
    url: SerializableHttpUrl


class ExternalUrlCreate(ExternalUrlBaseMixin, IdentifiableCreate):
    """Create model for external url."""

    @model_validator(mode="after")
    def validate_url(self):
        allowed_url = EXTERNAL_SOURCE_INFO[self.source]["allowed_url"]
        if not self.url.unicode_string().startswith(allowed_url):
            msg = f"The url for '{self.source}' must start with {allowed_url}"
            raise ValueError(msg)
        return self


ExternalUrlAdminUpdate = make_update_schema(
    ExternalUrlCreate,
    "ExternalUrlAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedExternalUrlRead(ExternalUrlBaseMixin, NestedIdentifiableRead):
    """Read model for nested external url."""

    @computed_field
    @property
    def source_name(self) -> str:
        return EXTERNAL_SOURCE_INFO[self.source]["name"]


class ExternalUrlRead(
    ExternalUrlBaseMixin,
    IdentifiableRead,
):
    """Read model for external url."""

    @computed_field
    @property
    def source_name(self) -> str:
        return EXTERNAL_SOURCE_INFO[self.source]["name"]
