from typing import Annotated

from app.db.model import CircuitExtractionExecution
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class CircuitExtractionExecutionFilter(
    CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CircuitExtractionExecution
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


CircuitExtractionExecutionFilterDep = Annotated[
    CircuitExtractionExecutionFilter, FilterDepends(CircuitExtractionExecutionFilter)
]
