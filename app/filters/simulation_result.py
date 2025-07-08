from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SimulationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    EntityFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
)


class NestedSimulationResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = SimulationResult


class SimulationResultFilter(EntityFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationResult
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SimulationResultFilterDep = Annotated[SimulationResultFilter, FilterDepends(SimulationResultFilter)]
NestedSimulationResultFilterDep = FilterDepends(
    with_prefix("simulation", NestedSimulationResultFilter)
)
