from datetime import datetime
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import ScientificArtifact
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    IdFilterMixin,
)
from app.filters.subject import SubjectFilterMixin


class ScientificArtifactFilterBase(CustomFilter):
    experiment_date__lte: datetime | None = None
    experiment_date__gte: datetime | None = None
    contact_email: str | None = None


class NestedScientificArtifactFilter(ScientificArtifactFilterBase, IdFilterMixin):
    class Constants(CustomFilter.Constants):
        model = ScientificArtifact


class ScientificArtifactFilter(
    ScientificArtifactFilterBase,
    SubjectFilterMixin,
    BrainRegionFilterMixin,
    EntityFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedScientificArtifactFilter.Constants):
        model = ScientificArtifact
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


ScientificArtifactFilterDep = Annotated[
    ScientificArtifactFilter, FilterDepends(ScientificArtifactFilter)
]
NestedScientificArtifactFilterDep = FilterDepends(
    with_prefix("scientific_artifact", NestedScientificArtifactFilter)
)
