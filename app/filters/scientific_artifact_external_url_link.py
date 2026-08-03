from typing import Annotated

from app.db.model import ScientificArtifactExternalUrlLink
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin
from app.filters.external_url import NestedExternalUrlFilter, NestedExternalUrlFilterDep
from app.filters.person import CreatorFilterMixin
from app.filters.scientific_artifact import (
    NestedScientificArtifactFilter,
    NestedScientificArtifactFilterDep,
)


class ScientificArtifactExternalUrlLinkFilter(
    IdFilterMixin,
    CreatorFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    external_url: Annotated[
        NestedExternalUrlFilter | None,
        NestedExternalUrlFilterDep,
    ] = None

    scientific_artifact: Annotated[
        NestedScientificArtifactFilter | None,
        NestedScientificArtifactFilterDep,
    ] = None

    class Constants(CustomFilter.Constants):
        model = ScientificArtifactExternalUrlLink
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
        ]


ScientificArtifactExternalUrlLinkFilterDep = Annotated[
    ScientificArtifactExternalUrlLinkFilter, FilterDepends(ScientificArtifactExternalUrlLinkFilter)
]
