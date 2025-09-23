from typing import TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema
from app.utils.doi import is_doi


class Author(TypedDict):
    """The name of authors of a publication."""

    given_name: str
    family_name: str


class PublicationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    DOI: str
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None


class PublicationCreate(PublicationBase):
    """Create model for publication."""

    @field_validator("DOI", mode="before")
    @classmethod
    def validate_doi(cls, value: str):
        """Check if DOI is valid and return it normalized."""
        if not is_doi(value):
            return ValueError(f"Invalid DOI format: {value}")

        return value


PublicationAdminUpdate = make_update_schema(
    PublicationCreate,
    "PublicationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedPublicationRead(
    PublicationBase,
    IdentifiableMixin,
):
    """Read model for nested publication."""


class PublicationRead(
    NestedPublicationRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    """Read model for publication."""
