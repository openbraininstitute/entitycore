import uuid
from typing import Annotated

from app.db.model import BrainAtlas, BrainAtlasRegion
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.species import SpeciesFilterMixin


class BrainAtlasFilter(
    EntityFilterMixin,
    NameFilterMixin,
    SpeciesFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    hierarchy_id: uuid.UUID | None = None
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainAtlas
        ordering_model_fields = ["name"]  # noqa: RUF012


class BrainAtlasRegionFilter(EntityFilterMixin, CustomFilter):
    is_leaf_region: bool | None = None
    brain_atlas_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainAtlasRegion
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


BrainAtlasFilterDep = Annotated[BrainAtlasFilter, FilterDepends(BrainAtlasFilter)]
BrainAtlasRegionFilterDep = Annotated[BrainAtlasRegionFilter, FilterDepends(BrainAtlasRegionFilter)]
