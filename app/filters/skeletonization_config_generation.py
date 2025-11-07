from typing import Annotated

from app.db.model import SkeletonizationConfigGeneration
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class SkeletonizationConfigGenerationFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SkeletonizationConfigGeneration
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


SkeletonizationConfigGenerationFilterDep = Annotated[
    SkeletonizationConfigGenerationFilter,
    FilterDepends(SkeletonizationConfigGenerationFilter),
]
