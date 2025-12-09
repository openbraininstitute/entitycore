import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SkeletonizationConfig
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class SkeletonizationConfigFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    pass


class NestedSkeletonizationConfigFilter(SkeletonizationConfigFilterBase):
    class Constants(CustomFilter.Constants):
        model = SkeletonizationConfig


class SkeletonizationConfigFilter(
    EntityFilterMixin, SkeletonizationConfigFilterBase, ILikeSearchFilterMixin
):
    skeletonization_campaign_id: uuid.UUID | None = None
    skeletonization_campaign_id__in: list[uuid.UUID] | None = None
    em_cell_mesh_id: uuid.UUID | None = None
    em_cell_mesh_id__in: list[uuid.UUID] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SkeletonizationConfig
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SkeletonizationConfigFilterDep = Annotated[
    SkeletonizationConfigFilter, FilterDepends(SkeletonizationConfigFilter)
]
NestedSkeletonizationConfigFilterDep = FilterDepends(
    with_prefix("skeletonization_config", NestedSkeletonizationConfigFilter)
)
