from typing import Annotated

from app.db.model import ScientificArtifactPublicationLink
from app.db.types import PublicationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin
from app.filters.person import CreatorFilterMixin
from app.filters.publication import NestedPublicationFilter, NestedPublicationFilterDep
from app.filters.scientific_artifact import (
    NestedScientificArtifactFilter,
    NestedScientificArtifactFilterDep,
)


class ScientificArtifactPublicationLinkFilter(
    IdFilterMixin,
    CreatorFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    publication_type: PublicationType | None = None

    publication: Annotated[
        NestedPublicationFilter | None,
        NestedPublicationFilterDep,
    ] = None

    scientific_artifact: Annotated[
        NestedScientificArtifactFilter | None,
        NestedScientificArtifactFilterDep,
    ] = None

    class Constants(CustomFilter.Constants):
        model = ScientificArtifactPublicationLink
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


ScientificArtifactPublicationLinkFilterDep = Annotated[
    ScientificArtifactPublicationLinkFilter, FilterDepends(ScientificArtifactPublicationLinkFilter)
]
