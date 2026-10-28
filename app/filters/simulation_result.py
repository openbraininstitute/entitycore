import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SimulationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class NestedSimulationResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = SimulationResult


class SimulationResultFilter(
    EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter
):
    simulation_id: uuid.UUID | None = None
    simulation_id__in: list[uuid.UUID] | None = None
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = SimulationResult
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]


SimulationResultFilterDep = Annotated[SimulationResultFilter, FilterDepends(SimulationResultFilter)]
NestedSimulationResultFilterDep = FilterDepends(
    with_prefix("simulation", NestedSimulationResultFilter)
)
