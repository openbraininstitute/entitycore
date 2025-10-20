import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SimulationCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.circuit import NestedCircuitFilter, NestedCircuitFilterDep
from app.filters.common import EntityFilterMixin, NameFilterMixin
from app.filters.simulation import NestedSimulationFilter


class SimulationCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    entity_id: uuid.UUID | None = None
    entity_id__in: list[uuid.UUID] | None = None

    circuit: Annotated[
        NestedCircuitFilter | None,
        NestedCircuitFilterDep,
    ] = None

    simulation: Annotated[
        NestedSimulationFilter | None,
        FilterDepends(with_prefix("simulation", NestedSimulationFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SimulationCampaignFilterDep = Annotated[
    SimulationCampaignFilter, FilterDepends(SimulationCampaignFilter)
]
