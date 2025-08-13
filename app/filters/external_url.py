from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ExternalUrl
from app.db.types import ExternalSource
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, CreatorFilterMixin, IdFilterMixin


class ExternalUrlFilter(
    CustomFilter,
    IdFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
):
    external_source: ExternalSource | None = None
    url: str | None = None

    order_by: list[str] = ["external_source"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalUrl
        ordering_model_fields = ["external_source"]  # noqa: RUF012


ExternalUrlFilterDep = Annotated[ExternalUrlFilter, FilterDepends(ExternalUrlFilter)]
