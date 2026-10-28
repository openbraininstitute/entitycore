from typing import Annotated

from app.db.model import BrainRegionHierarchy
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin
from app.filters.species import SpeciesFilterMixin


class BrainRegionHierarchyFilter(SpeciesFilterMixin, IdFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["name"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = BrainRegionHierarchy
        ordering_model_fields = ["name"]  # ruff:ignore[mutable-class-default]


BrainRegionHierarchyFilterDep = Annotated[
    BrainRegionHierarchyFilter, FilterDepends(BrainRegionHierarchyFilter)
]
