"""This module defines schemas for scientific artifacts."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BrainRegionRead
from app.schemas.entity import EntityRead


class PublicationType(StrEnum):
    """The type of publication for a scientific artifact."""

    entity_source = auto()
    component_source = auto()
    application = auto()


class Author(TypedDict):
    """The names of authors of a publication."""

    given_name: str
    family_name: str


# where was the artifact published?
class PublicationBase(EntityRead):
    """Represents ways to define or identify an entity.

    Fields include DOI, PMID, UUID, and other means.
    All fields are optional.
    """

    DOI: str | None = None  # Optional DOI (Digital Object Identifier) as a string
    PMID: int | None = None  # Optional PMID (PubMed Identifier) as an integer
    UUID: uuid.UUID | None = None  # Using uuid.UUID type for clarity
    original_source_location: str | None = None
    other_identifier: str | None = None  # Optional alternative identifier as a string
    title: str | None = None
    authors: list[Author] | None = None  # list of {"name", "lastname"} entries
    url: str | None = None
    journal: str | None = None
    publication_year: int | None = None
    abstract: str | None = None


class PublicationCreate(PublicationBase):
    """Create a publication."""


class ScientificArtifactPublicationLinkBase(BaseModel):
    """Based class for linking a scientific artifact to a publication."""

    publication_id: UUID
    publication_type: PublicationType
    scientific_artifact_id: UUID


class ScientificArtifactPublicationLinkCreate(ScientificArtifactPublicationLinkBase):
    """Create a link between a scientific artifact and a publication."""


class ScientificArtifactBase(EntityRead):
    """Base class for scientific artifacts."""

    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    subject_id: uuid.UUID | None = None
    license_id: UUID | None = None
    experiment_date: date | None = None
    contact_id: uuid.UUID | None = None


class ScientificArtifactCreate(ScientificArtifactBase):
    """Create a scientific artifact."""

    brain_region_id: uuid.UUID | None = None


class ScientificArtifactRead(ScientificArtifactBase):
    """Read a scientific artifact."""

    id: UUID
    brain_region: BrainRegionRead
    creation_date: datetime | None = None
    update_date: datetime | None = None
