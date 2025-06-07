from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import SimulationCampaign
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, NameFilterMixin
from app.filters.simulation import NestedSimulationFilter, NestedSimulationFilterDep


class SimulationCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    simulation: Annotated[NestedSimulationFilter | None, NestedSimulationFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SimulationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


SimulationCampaignFilterDep = Annotated[
    SimulationCampaignFilter, FilterDepends(SimulationCampaignFilter)
]
