from typing import Annotated

from app.db.model import SimulationGeneration
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class SimulationGenerationFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationGeneration
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


SimulationGenerationFilterDep = Annotated[
    SimulationGenerationFilter, FilterDepends(SimulationGenerationFilter)
]
