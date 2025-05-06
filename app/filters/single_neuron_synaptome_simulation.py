from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import SingleNeuronSynaptomeSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
)
from app.filters.single_neuron_synaptome import (
    NestedSingleNeuronSynaptomeFilterDep,
    SingleNeuronSynaptomeFilter,
)


class SingleNeuronSynaptomeSimulationFilter(
    CustomFilter,
    EntityFilterMixin,
    BrainRegionFilterMixin,
):
    status: SingleNeuronSimulationStatus | None = None

    synaptome: Annotated[
        SingleNeuronSynaptomeFilter | None, NestedSingleNeuronSynaptomeFilterDep
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptomeSimulation
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
SingleNeuronSynaptomeSimulationFilterDep = Annotated[
    SingleNeuronSynaptomeSimulationFilter, FilterDepends(SingleNeuronSynaptomeSimulationFilter)
]
