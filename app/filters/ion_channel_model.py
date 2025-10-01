from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import IonChannelModel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    NameFilterMixin,
    NestedBrainRegionFilter,
)
from app.filters.scientific_artifact import ScientificArtifactFilter
from app.filters.subject import NestedSubjectFilter


class NestedIonChannelModelFilter(
    IdFilterMixin,
    NameFilterMixin,
    CustomFilter,
):
    brain_region: Annotated[
        NestedBrainRegionFilter | None,
        FilterDepends(with_prefix("morphology__brain_region", NestedBrainRegionFilter)),
    ] = None
    subject: Annotated[
        NestedSubjectFilter | None,
        FilterDepends(with_prefix("morphology__subject", NestedSubjectFilter)),
    ] = None

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
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
IonChannelModelFilterDep = Annotated[IonChannelModelFilter, FilterDepends(IonChannelModelFilter)]
