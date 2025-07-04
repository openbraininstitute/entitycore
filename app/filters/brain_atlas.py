from typing import Annotated

from app.db.model import BrainAtlas, BrainAtlasRegion
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin, SpeciesFilterMixin


class BrainAtlasFilter(IdFilterMixin, NameFilterMixin, SpeciesFilterMixin, CustomFilter):
    order_by: list[str] = ["name"]

    class Constants(CustomFilter.Constants):
        model = BrainAtlas
        ordering_model_fields = ["name"]


class BrainAtlasRegionFilter(IdFilterMixin, CustomFilter):
    order_by: list[str] = ["id", "creation_date"]

    class Constants(CustomFilter.Constants):
        model = BrainAtlasRegion
        ordering_model_fields = ["creation_date"]


BrainAtlasFilterDep = Annotated[BrainAtlasFilter, FilterDepends(BrainAtlasFilter)]
BrainAtlasRegionFilterDep = Annotated[BrainAtlasRegionFilter, FilterDepends(BrainAtlasRegionFilter)]
