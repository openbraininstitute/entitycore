from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ExternalDataSourcePage
from app.db.types import ExternalDataSource
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, CreatorFilterMixin, IdFilterMixin


class ExternalDataSourcePageFilter(
    CustomFilter,
    IdFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
):
    source_label: ExternalDataSource | None = None
    url: str | None = None

    order_by: list[str] = ["source_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalDataSourcePage
        ordering_model_fields = ["source_label"]  # noqa: RUF012


ExternalDataSourcePageFilterDep = Annotated[
    ExternalDataSourcePageFilter, FilterDepends(ExternalDataSourcePageFilter)
]
