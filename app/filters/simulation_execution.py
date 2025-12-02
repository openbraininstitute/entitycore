from typing import Annotated

from app.db.model import SimulationExecution
from app.db.types import SimulationExecutionStatus
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class SimulationExecutionFilter(CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    status: SimulationExecutionStatus | None = None

    class Constants(CustomFilter.Constants):
        model = SimulationExecution
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


SimulationExecutionFilterDep = Annotated[
    SimulationExecutionFilter, FilterDepends(SimulationExecutionFilter)
]
