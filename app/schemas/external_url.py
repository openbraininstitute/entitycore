from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer, model_validator

from app.db.types import ALLOWED_URLS_PER_EXTERNAL_SOURCE, ExternalSource
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin


class ExternalUrlBase(BaseModel):
    """Base model for external url."""

    model_config = ConfigDict(from_attributes=True)
    source: ExternalSource
    url: HttpUrl
    title: str | None = None

    @field_serializer("url")
    def serialize_url(self, url: HttpUrl) -> str:  # noqa: PLR6301
        """Return the url as string for serialization to the db."""
        return url.unicode_string()


class ExternalUrlCreate(ExternalUrlBase):
    """Create model for external url."""

    @model_validator(mode="after")
    def validate_url(self):
        allowed_url = ALLOWED_URLS_PER_EXTERNAL_SOURCE.get(self.source)
        if allowed_url is None:
            msg = f"There are no allowed urls defined for '{self.source}'"
            raise ValueError(msg)
        if not self.url.unicode_string().startswith(allowed_url):
            msg = f"The url for '{self.source}' must start with {allowed_url}"
            raise ValueError(msg)
        return self


class NestedExternalUrlRead(
    ExternalUrlBase,
    IdentifiableMixin,
):
    """Read model for nested external url."""


class ExternalUrlRead(
    NestedExternalUrlRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    """Read model for external url."""
