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
from app.filters.memodel import NestedMEModelFilter, NestedMEModelFilterDep


class SingleNeuronSimulationFilter(
    CustomFilter,
    EntityFilterMixin,
    BrainRegionFilterMixin,
    NameFilterMixin,
):
    status: SingleNeuronSimulationStatus | None = None

    me_model: Annotated[NestedMEModelFilter | None, NestedMEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSimulation
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "status",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
        ]


# Dependencies
SingleNeuronSimulationFilterDep = Annotated[
    SingleNeuronSimulationFilter, FilterDepends(SingleNeuronSimulationFilter)
]
