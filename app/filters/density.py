import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import (
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
)
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    ContributionFilterMixin,
    CreationFilterMixin,
    ETypeClassFilterMixin,
    MTypeClassFilterMixin,
    SpeciesFilterMixin,
    StrainFilterMixin,
    SynapticPathwayFilterMixin,
)


class DensityFilterBase(
    CustomFilter,
    StrainFilterMixin,
    SpeciesFilterMixin,
    CreationFilterMixin,
    BrainRegionFilterMixin,
    ContributionFilterMixin,
):
    id__in: list[uuid.UUID] | None = None
    name__ilike: str | None = None
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
    SynapticPathwayFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = ExperimentalSynapsesPerConnection
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


ExperimentalSynapsesPerConnectionFilterDep = Annotated[
    ExperimentalSynapsesPerConnectionFilter, FilterDepends(ExperimentalSynapsesPerConnectionFilter)
]
