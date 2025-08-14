from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import ExternalUrl
from app.db.types import ExternalSource
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, CreatorFilterMixin, IdFilterMixin


class NestedExternalUrlFilter(
    IdFilterMixin,
    CustomFilter,
):
    source: ExternalSource | None = None
    url: str | None = None
    title: str | None = None

    class Constants(CustomFilter.Constants):
        model = ExternalUrl


class ExternalUrlFilter(
    CreatorFilterMixin,
    CreationFilterMixin,
    NestedExternalUrlFilter,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedExternalUrlFilter.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "source",
            "url",
            "title",
        ]


ExternalUrlFilterDep = Annotated[ExternalUrlFilter, FilterDepends(ExternalUrlFilter)]
NestedExternalUrlFilterDep = FilterDepends(with_prefix("external_url", NestedExternalUrlFilter))
