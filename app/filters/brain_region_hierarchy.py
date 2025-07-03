from typing import Annotated

from app.db.model import BrainRegionHierarchy
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin


class BrainRegionHierarchyFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainRegionHierarchy
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionHierarchyFilterDep = Annotated[
    BrainRegionHierarchyFilter, FilterDepends(BrainRegionHierarchyFilter)
]
