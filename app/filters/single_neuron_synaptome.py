from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import SingleNeuronSynaptome
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin, NestedBrainRegionFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin
from app.filters.memodel import NestedMEModelFilter, NestedMEModelFilterDep


class NestedSingleNeuronSynaptomeFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("synaptome__brain_region", NestedBrainRegionFilter)),
    ] = None

    me_model: Annotated[
        NestedMEModelFilter | None,
        FilterDepends(with_prefix("synaptome__me_model", NestedMEModelFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome


class SingleNeuronSynaptomeFilter(
    EntityFilterMixin,
    NameFilterMixin,
    BrainRegionFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    me_model: Annotated[NestedMEModelFilter | None, NestedMEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
        ]


# Dependencies
SingleNeuronSynaptomeFilterDep = Annotated[
    SingleNeuronSynaptomeFilter, FilterDepends(SingleNeuronSynaptomeFilter)
]
# Nested dependencies
NestedSingleNeuronSynaptomeFilterDep = FilterDepends(
    with_prefix("synaptome", NestedSingleNeuronSynaptomeFilter)
)
