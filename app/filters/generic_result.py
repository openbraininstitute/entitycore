# app/filters/generic_result
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import GenericResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class NestedGenericResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = GenericResult


class GenericResultFilter(EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = GenericResult
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


GenericResultFilterDep = Annotated[GenericResultFilter, FilterDepends(GenericResultFilter)]
NestedGenericResultFilterDep = FilterDepends(
    with_prefix("generic_result", NestedGenericResultFilter)
)
