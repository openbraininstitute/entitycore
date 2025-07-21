from enum import StrEnum, auto
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


class PublicationType(StrEnum):
    """The type of of the relation between publication and a scientific artifact.

    entity_source: The artefact is published with this publication.
    component_source: The publication is used to generate the artifact.
    application: The publication uses the artifact.
    """

    entity_source = auto()
    component_source = auto()
    application = auto()


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


class PublicationRead(
    PublicationBase,
    CreationMixin,
    IdentifiableMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
):
    pass
