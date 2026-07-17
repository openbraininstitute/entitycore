from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import ExternalUrl
from app.db.types import ExternalSource
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.person import CreatorFilterMixin


class NestedExternalUrlFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    source: ExternalSource | None = None
    url: str | None = None

    class Constants(CustomFilter.Constants):
        model = ExternalUrl


class ExternalUrlFilter(
    CreatorFilterMixin,
    CreationFilterMixin,
    NestedExternalUrlFilter,
    ILikeSearchFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(NestedExternalUrlFilter.Constants):
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "source",
            "url",
            "name",
        ]


ExternalUrlFilterDep = Annotated[ExternalUrlFilter, FilterDepends(ExternalUrlFilter)]
NestedExternalUrlFilterDep = FilterDepends(with_prefix("external_url", NestedExternalUrlFilter))
