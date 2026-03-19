from typing import Annotated

from app.db.model import IonChannelModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
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


class IonChannelModelFilter(ScientificArtifactFilter, NameFilterMixin, ILikeSearchFilterMixin):
    nmodl_suffix: str | None = None

    is_ljp_corrected: bool | None = None
    is_temperature_dependent: bool | None = None
    temperature_celsius: int | None = None
    temperature_celsius__lte: int | None = None
    temperature_celsius__gte: int | None = None
    is_stochastic: bool | None = None
    conductance_name: str | None = None
    conductance_name__isnull: bool | None = None
    max_permeability_name: str | None = None
    max_permeability_name__isnull: bool | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = IonChannelModel
        ordering_model_fields = [  # noqa: RUF012
            "id",
            "creation_date",
            "update_date",
            "name",
            "nmodl_suffix",
            "is_ljp_corrected",
            "is_temperature_dependent",
            "temperature_celsius",
            "is_stochastic",
            "conductance_name",
            "max_permeability_name",
            "brain_region__name",
            "brain_region__acronym",
            "subject__name",
            "subject__species__name",
            "subject__strain__name",
            "created_by__pref_label",
            "updated_by__pref_label",
        ]


# Dependencies
IonChannelModelFilterDep = Annotated[IonChannelModelFilter, FilterDepends(IonChannelModelFilter)]
