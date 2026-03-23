from typing import Annotated

from app.db.model import (
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    Measurement,
)
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin, NestedBrainRegionFilter
from app.filters.common import (
    ETypeClassFilterMixin,
    ILikeSearchFilterMixin,
    MTypeClassFilterMixin,
    NameFilterMixin,
    NestedMTypeClassFilter,
    with_prefix,
)
from app.filters.entity import EntityFilterMixin
from app.filters.subject import SubjectFilterMixin


class NestedMeasurementFilter(CustomFilter):
    """Nested filter for measurement sorting."""

    class Constants(CustomFilter.Constants):
        model = Measurement
        ordering_model_fields = ["value"]  # noqa: RUF012


class DensityFilterBase(
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    NameFilterMixin,
    ILikeSearchFilterMixin,
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
            "mtype__pref_label",
            "etype__pref_label",
            "subject__strain__name",
        ]


ExperimentalNeuronDensityFilterDep = Annotated[
    ExperimentalNeuronDensityFilter, FilterDepends(ExperimentalNeuronDensityFilter)
]


class ExperimentalBoutonDensityFilter(
    DensityFilterBase,
    MTypeClassFilterMixin,
):
    # Measurement filters for sorting support
    measurement_mean: Annotated[
        NestedMeasurementFilter | None,
        FilterDepends(with_prefix("measurement_mean", NestedMeasurementFilter)),
    ] = None
    measurement_sem: Annotated[
        NestedMeasurementFilter | None,
        FilterDepends(with_prefix("measurement_sem", NestedMeasurementFilter)),
    ] = None
    measurement_sample_size: Annotated[
        NestedMeasurementFilter | None,
        FilterDepends(with_prefix("measurement_sample_size", NestedMeasurementFilter)),
    ] = None

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
            "mtype__pref_label",
            "subject__strain__name",
            "measurement_mean__value",
            "measurement_sem__value",
            "measurement_sample_size__value",
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
            "update_date",
            "name",
            "subject__species__name",
            "subject__age_value",
            "brain_region__name",
            "brain_region__acronym",
            "pre_region__name",
            "pre_region__acronym",
            "post_region__name",
            "post_region__acronym",
            "pre_mtype__pref_label",
            "post_mtype__pref_label",
        ]


ExperimentalSynapsesPerConnectionFilterDep = Annotated[
    ExperimentalSynapsesPerConnectionFilter, FilterDepends(ExperimentalSynapsesPerConnectionFilter)
]
