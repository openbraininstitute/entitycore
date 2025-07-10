from typing import Annotated

from app.db.model import SingleNeuronSynaptomeSimulation
from app.db.types import SingleNeuronSimulationStatus
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
)
from app.filters.single_neuron_synaptome import (
    NestedSingleNeuronSynaptomeFilter,
    NestedSingleNeuronSynaptomeFilterDep,
)


class SingleNeuronSynaptomeSimulationFilter(
    CustomFilter,
    EntityFilterMixin,
    BrainRegionFilterMixin,
    NameFilterMixin,
):
    status: SingleNeuronSimulationStatus | None = None

    synaptome: Annotated[
        NestedSingleNeuronSynaptomeFilter | None, NestedSingleNeuronSynaptomeFilterDep
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptomeSimulation
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
        ]


# Dependencies
SingleNeuronSynaptomeSimulationFilterDep = Annotated[
    SingleNeuronSynaptomeSimulationFilter, FilterDepends(SingleNeuronSynaptomeSimulationFilter)
]
