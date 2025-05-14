import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import IonChannelModel
from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    CreationFilterMixin,
    NestedSpeciesFilterDep,
    SpeciesFilter,
)


class IonChannelModelFilter(
    CustomFilter,
    CreationFilterMixin,
    BrainRegionFilterMixin,
):
    nmodl_suffix: str | None = None
    species_id__in: list[uuid.UUID] | None = None
    species: Annotated[SpeciesFilter | None, NestedSpeciesFilterDep] = None

    is_ljp_corrected: bool | None = None
    is_temperature_dependent: bool | None = None
    temperature_celsius__lte: int | None = None
    temperature_celsius__gte: int | None = None
    is_stochastic: bool | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
IonChannelModelFilterDep = Annotated[IonChannelModelFilter, FilterDepends(IonChannelModelFilter)]
