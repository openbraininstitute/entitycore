from typing import Annotated

from app.db.model import SkeletonizationCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.skeletonization_config import (
    NestedSkeletonizationConfigFilter,
    NestedSkeletonizationConfigFilterDep,
)


class SkeletonizationCampaignFilter(
    CustomFilter, EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin
):
    skeletonization_config: Annotated[
        NestedSkeletonizationConfigFilter | None,
        NestedSkeletonizationConfigFilterDep,
    ] = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = SkeletonizationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]


SkeletonizationCampaignFilterDep = Annotated[
    SkeletonizationCampaignFilter, FilterDepends(SkeletonizationCampaignFilter)
]
