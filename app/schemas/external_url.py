from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    computed_field,
    field_serializer,
    model_validator,
)

from app.db.types import EXTERNAL_SOURCE_INFO, ExternalSource
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin


class ExternalUrlBase(BaseModel):
    """Base model for external url."""

    model_config = ConfigDict(from_attributes=True)
    source: ExternalSource
    url: HttpUrl
    name: str
    description: str

    @field_serializer("url")
    def serialize_url(self, url: HttpUrl) -> str:  # noqa: PLR6301
        """Return the url as string for serialization to the db."""
        return url.unicode_string()


class ExternalUrlCreate(ExternalUrlBase):
    """Create model for external url."""

    @model_validator(mode="after")
    def validate_url(self):
        allowed_url = EXTERNAL_SOURCE_INFO[self.source]["allowed_url"]
        if not self.url.unicode_string().startswith(allowed_url):
            msg = f"The url for '{self.source}' must start with {allowed_url}"
            raise ValueError(msg)
        return self


class NestedExternalUrlRead(
    ExternalUrlBase,
    IdentifiableMixin,
):
    """Read model for nested external url."""

    @computed_field
    @property
    def source_label(self) -> str:
        return EXTERNAL_SOURCE_INFO[self.source]["label"]


class ExternalUrlRead(
    NestedExternalUrlRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    """Read model for external url."""
