from typing import Annotated

from app.db.model import IonChannelModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    NameFilterMixin,
)
from app.filters.scientific_artifact import ScientificArtifactFilter


class NestedIonChannelModelFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    class Constants(CustomFilter.Constants):
        model = IonChannelModel


class IonChannelModelFilter(ScientificArtifactFilter, NameFilterMixin):
    nmodl_suffix: str | None = None

    is_ljp_corrected: bool | None = None
    is_temperature_dependent: bool | None = None
    temperature_celsius__lte: int | None = None
    temperature_celsius__gte: int | None = None
    is_stochastic: bool | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = IonChannelModel
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
        ]


# Dependencies
IonChannelModelFilterDep = Annotated[IonChannelModelFilter, FilterDepends(IonChannelModelFilter)]
