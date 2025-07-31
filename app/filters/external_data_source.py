import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ExternalDataSource, ExternalDataSourcePage
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin


class ExternalDataSourceFilter(
    CustomFilter,
    EntityFilterMixin,
):
    label: str
    URL: str

    order_by: list[str] = ["label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalDataSource
        ordering_model_fields = ["label"]  # noqa: RUF012


ExternalDataSourceFilterDep = Annotated[
    ExternalDataSourceFilter, FilterDepends(ExternalDataSourceFilter)
]


class ExternalDataSourcePageFilter(
    CustomFilter,
    EntityFilterMixin,
):
    external_data_source_id: uuid.UUID
    URL: str

    order_by: list[str] = ["external_data_source_id"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalDataSourcePage
        ordering_model_fields = ["external_data_source_id"]  # noqa: RUF012


ExternalDataSourcePageFilterDep = Annotated[
    ExternalDataSourcePageFilter, FilterDepends(ExternalDataSourcePageFilter)
]
