from typing import Annotated

from app.db.model import (
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
)
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedBrainRegionFilter,
    NestedMTypeClassFilter,
    with_prefix,
)
from app.filters.subject import SubjectFilterMixin


class DensityFilterBase(
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012


class ExperimentalNeuronDensityFilter(
    DensityFilterBase,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = ExperimentalNeuronDensity
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "subject__species__name",
            "subject__age_value",
        ]


ExperimentalNeuronDensityFilterDep = Annotated[
    ExperimentalNeuronDensityFilter, FilterDepends(ExperimentalNeuronDensityFilter)
]


class ExperimentalBoutonDensityFilter(
    DensityFilterBase,
    MTypeClassFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = ExperimentalBoutonDensity
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "brain_region__name",
            "brain_region__acronym",
            "subject__species__name",
            "subject__age_value",
        ]


ExperimentalBoutonDensityFilterDep = Annotated[
    ExperimentalBoutonDensityFilter, FilterDepends(ExperimentalBoutonDensityFilter)
]


class ExperimentalSynapsesPerConnectionFilter(
    DensityFilterBase,
):
    pre_mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("pre_mtype", NestedMTypeClassFilter)),
    ] = None
    post_mtype: Annotated[
        NestedMTypeClassFilter | None,
        FilterDepends(with_prefix("post_mtype", NestedMTypeClassFilter)),
    ] = None
    pre_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("pre_region", NestedBrainRegionFilter)),
    ] = None
    post_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("post_region", NestedBrainRegionFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = ExperimentalSynapsesPerConnection
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "subject__age_value",
            "brain_region__name",
            "brain_region__acronym",
        ]


ExperimentalSynapsesPerConnectionFilterDep = Annotated[
    ExperimentalSynapsesPerConnectionFilter, FilterDepends(ExperimentalSynapsesPerConnectionFilter)
]
