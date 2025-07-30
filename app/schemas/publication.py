from typing import TypedDict

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class Author(TypedDict):
    """The name of authors of a publication."""

    given_name: str
    family_name: str


class PublicationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    DOI: str | None = None
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None


class PublicationCreate(PublicationBase):
    pass


class NestedPublicationRead(PublicationBase, IdentifiableMixin):
    pass


class PublicationRead(
    NestedPublicationRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
):
    pass
