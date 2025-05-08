import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import BrainRegionHierarchyName
from app.filters.base import CustomFilter
from app.filters.common import NameFilterMixin


class BrainRegionNameFilter(NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None
    name: str | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainRegionHierarchyName
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionNameFilterDep = Annotated[BrainRegionNameFilter, FilterDepends(BrainRegionNameFilter)]
