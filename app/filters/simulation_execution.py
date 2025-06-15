from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import SimulationExecution
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class SimulationExecutionFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    status: str | None = None

    class Constants(CustomFilter.Constants):
        model = SimulationExecution
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


SimulationExecutionFilterDep = Annotated[
    SimulationExecutionFilter, FilterDepends(SimulationExecutionFilter)
]
