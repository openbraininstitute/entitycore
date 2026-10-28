from typing import TypedDict

from pydantic import field_validator

from app.schemas.base import (
    Schema,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema
from app.utils.doi import is_doi


class Author(TypedDict):
    """The name of authors of a publication."""

    given_name: str
    family_name: str


class PublicationBase(Schema):
    DOI: str
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None


class PublicationCreate(PublicationBase, IdentifiableCreate):
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
    NestedIdentifiableRead,
):
    """Read model for nested publication."""


class PublicationRead(
    PublicationBase,
    IdentifiableRead,
):
    """Read model for publication."""
