from typing import Annotated

from app.db.model import SingleNeuronSynaptome
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter, Prefix
from app.filters.brain_region import BrainRegionFilterMixin
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin
from app.filters.memodel import NestedMEModelFilter


class NestedSingleNeuronSynaptomeFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    me_model: Annotated[NestedMEModelFilter | None, Prefix("synaptome__me_model")] = None

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome


class SingleNeuronSynaptomeFilter(
    EntityFilterMixin,
    NameFilterMixin,
    BrainRegionFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    me_model: NestedMEModelFilter | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = SingleNeuronSynaptome
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "created_by__pref_label",
            "me_model__etype__pref_label",
            "me_model__mtype__pref_label",
        ]


# Dependencies
SingleNeuronSynaptomeFilterDep = Annotated[
    SingleNeuronSynaptomeFilter, FilterDepends(SingleNeuronSynaptomeFilter)
]
