import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ExternalDatabase, ExternalDatabaseURL
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin


class ExternalDatabaseFilter(
    CustomFilter,
    EntityFilterMixin,
):
    label: str
    URL: str

    order_by: list[str] = ["label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalDatabase
        ordering_model_fields = ["label"]  # noqa: RUF012


ExternalDatabaseFilterDep = Annotated[ExternalDatabaseFilter, FilterDepends(ExternalDatabaseFilter)]


class ExternalDatabaseURLFilter(
    CustomFilter,
    EntityFilterMixin,
):
    external_database_id: uuid.UUID
    URL: str

    order_by: list[str] = ["external_database_id"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ExternalDatabaseURL
        ordering_model_fields = ["external_database_id"]  # noqa: RUF012


ExternalDatabaseURLFilterDep = Annotated[
    ExternalDatabaseURLFilter, FilterDepends(ExternalDatabaseURLFilter)
]
