from pydantic import BaseModel, HttpUrl, model_validator

from app.db.types import ALLOWED_URLS_PER_EXTERNAL_SOURCE, ExternalSource
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin


class ExternalUrlBase(BaseModel):
    """Base model for external url."""

    source: ExternalSource
    url: HttpUrl
    title: str | None = None


class ExternalUrlRead(ExternalUrlBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin):
    """Read model for external url."""


class ExternalUrlCreate(ExternalUrlBase):
    """Create model for external url."""

    @model_validator(mode="after")
    def validate_url(self):
        allowed_url = ALLOWED_URLS_PER_EXTERNAL_SOURCE.get(self.source)
        if allowed_url is None:
            msg = f"There are no allowed urls defined for '{self.source}'"
            raise ValueError(msg)
        if not self.url.unicode_string().startswith(allowed_url):
            msg = f"The url must start with {allowed_url} for '{self.source}'"
            raise ValueError(msg)
        return self
