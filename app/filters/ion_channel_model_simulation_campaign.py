from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import IonChannelModelSimulationCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.simulation import NestedSimulationFilter


class IonChannelModelSimulationCampaignFilter(
    CustomFilter, EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin
):
    simulation: Annotated[
        NestedSimulationFilter | None,
        FilterDepends(with_prefix("simulation", NestedSimulationFilter)),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelModelSimulationCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


IonChannelModelSimulationCampaignFilterDep = Annotated[
    IonChannelModelSimulationCampaignFilter, FilterDepends(IonChannelModelSimulationCampaignFilter)
]
