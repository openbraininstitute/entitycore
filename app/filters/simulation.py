import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Simulation
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.circuit import NestedCircuitFilter, NestedCircuitFilterDep
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class SimulationFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    entity_id: uuid.UUID | None = None
    entity_id__in: list[uuid.UUID] | None = None


class NestedSimulationFilter(SimulationFilterBase):
    class Constants(CustomFilter.Constants):
        model = Simulation


class SimulationFilter(EntityFilterMixin, SimulationFilterBase, ILikeSearchFilterMixin):
    simulation_campaign_id: uuid.UUID | None = None
    simulation_campaign_id__in: list[uuid.UUID] | None = None

    circuit: Annotated[NestedCircuitFilter | None, NestedCircuitFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Simulation
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SimulationFilterDep = Annotated[SimulationFilter, FilterDepends(SimulationFilter)]
NestedSimulationFilterDep = FilterDepends(with_prefix("simulation", NestedSimulationFilter))
