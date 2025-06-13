from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import SimulationResult
from app.filters.base import CustomFilter
from app.filters.common import (
    ContributionFilterMixin,
    CreationFilterMixin,
    CreatorFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
)


class NestedSimulationResultFilter(CustomFilter, IdFilterMixin, NameFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationResult
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


class SimulationResultFilter(
    NestedSimulationResultFilter, CreationFilterMixin, CreatorFilterMixin, ContributionFilterMixin
):
    pass


SimulationResultFilterDep = Annotated[SimulationResultFilter, FilterDepends(SimulationResultFilter)]
NestedSimulationResultFilterDep = FilterDepends(
    with_prefix("simulation", NestedSimulationResultFilter)
)
