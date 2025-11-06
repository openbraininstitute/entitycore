from typing import Annotated

from app.db.model import SkeletonizationCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, NameFilterMixin
from app.filters.skeletonization_config import (
    NestedSkeletonizationConfigFilter,
    NestedSkeletonizationConfigFilterDep,
)


class SkeletonizationCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    skeletonization_config: Annotated[
        NestedSkeletonizationConfigFilter | None,
        NestedSkeletonizationConfigFilterDep,
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SkeletonizationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SkeletonizationCampaignFilterDep = Annotated[
    SkeletonizationCampaignFilter, FilterDepends(SkeletonizationCampaignFilter)
]
