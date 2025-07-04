from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SimulationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    ContributionFilterMixin,
    CreationFilterMixin,
    CreatorFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
)


class NestedSimulationResultFilter(CustomFilter, IdFilterMixin, NameFilterMixin):
    order_by: list[str] = ["-creation_date"]

    class Constants(CustomFilter.Constants):
        model = SimulationResult
        ordering_model_fields = ["creation_date", "update_date", "name"]


class SimulationResultFilter(
    NestedSimulationResultFilter, CreationFilterMixin, CreatorFilterMixin, ContributionFilterMixin
):
    pass


SimulationResultFilterDep = Annotated[SimulationResultFilter, FilterDepends(SimulationResultFilter)]
NestedSimulationResultFilterDep = FilterDepends(
    with_prefix("simulation", NestedSimulationResultFilter)
)
