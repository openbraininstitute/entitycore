from typing import Annotated

from app.db.model import SingleNeuronSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
)
from app.filters.memodel import MEModelFilter, NestedMEModelFilterDep


class SingleNeuronSimulationFilter(
    CustomFilter,
    EntityFilterMixin,
    BrainRegionFilterMixin,
    NameFilterMixin,
):
    status: SingleNeuronSimulationStatus | None = None

    me_model: Annotated[MEModelFilter | None, NestedMEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSimulation
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
SingleNeuronSimulationFilterDep = Annotated[
    SingleNeuronSimulationFilter, FilterDepends(SingleNeuronSimulationFilter)
]
