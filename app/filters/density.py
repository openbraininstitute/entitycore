from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import (
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
)
from app.filters.base import CustomFilter, with_nested_prefix
from app.filters.common import (
    BrainRegionFilter,
    BrainRegionFilterMixin,
    EntityFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilter,
    MTypeClassFilterMixin,
    NameFilterMixin,
    SubjectFilterMixin,
)


class DensityFilterBase(
    CustomFilter,
    EntityFilterMixin,
    BrainRegionFilterMixin,
    SubjectFilterMixin,
    NameFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012


class ExperimentalNeuronDensityFilter(
    DensityFilterBase,
    MTypeClassFilterMixin,
    ETypeClassFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = ExperimentalNeuronDensity
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ExperimentalNeuronDensityFilterDep = Annotated[
    ExperimentalNeuronDensityFilter, FilterDepends(ExperimentalNeuronDensityFilter)
]


class ExperimentalBoutonDensityFilter(
    DensityFilterBase,
    MTypeClassFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = ExperimentalBoutonDensity
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ExperimentalBoutonDensityFilterDep = Annotated[
    ExperimentalBoutonDensityFilter, FilterDepends(ExperimentalBoutonDensityFilter)
]


class ExperimentalSynapsesPerConnectionFilter(
    DensityFilterBase,
):
    pre_mtype: Annotated[
        MTypeClassFilter | None, FilterDepends(with_nested_prefix("pre_mtype", MTypeClassFilter))
    ] = None
    post_mtype: Annotated[
        MTypeClassFilter | None, FilterDepends(with_nested_prefix("post_mtype", MTypeClassFilter))
    ] = None
    pre_region: Annotated[
        BrainRegionFilter | None, FilterDepends(with_nested_prefix("pre_region", BrainRegionFilter))
    ] = None
    post_region: Annotated[
        BrainRegionFilter | None,
        FilterDepends(with_nested_prefix("post_region", BrainRegionFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = ExperimentalSynapsesPerConnection
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ExperimentalSynapsesPerConnectionFilterDep = Annotated[
    ExperimentalSynapsesPerConnectionFilter, FilterDepends(ExperimentalSynapsesPerConnectionFilter)
]
