from typing import TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)
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
    @field_validator("DOI", mode="before")
    @classmethod
    def validate_doi(cls, value: str):
        """Check if DOI is valid and return it normalized."""
        if not is_doi(value):
            return ValueError(f"Invalid DOI format: {value}")

        return value


class NestedPublicationRead(PublicationBase, IdentifiableMixin):
    pass


class PublicationRead(
    NestedPublicationRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    pass
