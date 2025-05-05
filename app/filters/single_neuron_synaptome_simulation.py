import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import SingleNeuronSynaptomeSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.filters.base import CustomFilter
from app.filters.common import AgentFilter, CreationFilterMixin, NestedAgentFilterDep
from app.filters.single_neuron_synaptome import (
    NestedSingleNeuronSynaptomeFilterDep,
    SingleNeuronSynaptomeFilter,
)


class SingleNeuronSynaptomeSimulationFilter(
    CustomFilter,
    CreationFilterMixin,
):
    id__in: list[uuid.UUID] | None = None
    name__ilike: str | None = None
    brain_region_id: int | None = None
    status: SingleNeuronSimulationStatus | None = None

    contribution: Annotated[AgentFilter | None, NestedAgentFilterDep] = None
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
