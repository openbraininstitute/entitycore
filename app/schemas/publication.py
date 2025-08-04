from typing import TypedDict

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin


class Author(TypedDict):
    """The name of authors of a publication."""

    given_name: str
    family_name: str


class PublicationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    DOI: str | None = None
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None


class PublicationCreate(PublicationBase, AuthorizationOptionalPublicMixin):
    pass


class NestedPublicationRead(
    PublicationBase, IdentifiableMixin, AuthorizationMixin, EntityTypeMixin
):
    pass


class PublicationRead(
    NestedPublicationRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
):
    pass
