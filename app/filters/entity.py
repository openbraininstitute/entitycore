from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import Entity
from app.db.types import EntityType
from app.filters.base import CustomFilter


class BasicEntityFilter(CustomFilter):
    type: EntityType | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Entity
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


BasicEntityFilterDep = Annotated[BasicEntityFilter, FilterDepends(BasicEntityFilter)]
