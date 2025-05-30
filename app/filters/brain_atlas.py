from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import BrainAtlas, BrainAtlasRegion
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin, SpeciesFilterMixin


class BrainAtlasFilter(IdFilterMixin, NameFilterMixin, SpeciesFilterMixin, CustomFilter):
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainAtlas
        ordering_model_fields = ["name"]  # noqa: RUF012


class BrainAtlasRegionFilter(IdFilterMixin, CustomFilter):
    order_by: list[str] = ["id", "creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainAtlasRegion
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


BrainAtlasFilterDep = Annotated[BrainAtlasFilter, FilterDepends(BrainAtlasFilter)]
BrainAtlasRegionFilterDep = Annotated[BrainAtlasRegionFilter, FilterDepends(BrainAtlasRegionFilter)]
