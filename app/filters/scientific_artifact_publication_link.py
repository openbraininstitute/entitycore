from typing import Annotated

from app.db.model import ScientificArtifactPublicationLink
from app.db.types import PublicationType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin
from app.filters.platform_user import CreatorFilterMixin
from app.filters.publication import NestedPublicationFilter
from app.filters.scientific_artifact import (
    NestedScientificArtifactFilter,
)


class ScientificArtifactPublicationLinkFilter(
    IdFilterMixin,
    CreatorFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    publication_type: PublicationType | None = None

    publication: NestedPublicationFilter | None = None

    scientific_artifact: NestedScientificArtifactFilter | None = None

    class Constants(CustomFilter.Constants):
        model = ScientificArtifactPublicationLink
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
        ]


ScientificArtifactPublicationLinkFilterDep = Annotated[
    ScientificArtifactPublicationLinkFilter, FilterDepends(ScientificArtifactPublicationLinkFilter)
]
