from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import Mesh as BrainRegionMesh
from app.filters.base import CustomFilter
from app.filters.common import BrainRegionFilterMixin, EntityFilterMixin


class BrainRegionMeshFilter(CustomFilter, BrainRegionFilterMixin, EntityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainRegionMesh
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


BrainRegionMeshFilterDep = Annotated[BrainRegionMeshFilter, FilterDepends(BrainRegionMeshFilter)]
