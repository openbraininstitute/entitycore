from typing import Annotated

from app.db.model import CellComposition
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    EntityFilterMixin,
    NameFilterMixin,
)


class CellCompositionFilter(
    CustomFilter,
    EntityFilterMixin,
    NameFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CellComposition
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CellCompositionFilterDep = Annotated[CellCompositionFilter, FilterDepends(CellCompositionFilter)]
