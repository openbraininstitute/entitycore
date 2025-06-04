from enum import StrEnum, auto
from typing import TypedDict


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
