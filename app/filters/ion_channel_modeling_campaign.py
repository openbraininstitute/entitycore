from typing import Annotated

from app.db.model import IonChannelModelingCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, NameFilterMixin
from app.filters.ion_channel_modeling import (
    NestedIonChannelModelingFilter,
    NestedIonChannelModelingFilterDep,
)


class IonChannelModelingCampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin):
    ion_channel_modeling: Annotated[
        NestedIonChannelModelingFilter | None, NestedIonChannelModelingFilterDep
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


IonChannelModelingCampaignFilterDep = Annotated[
    IonChannelModelingCampaignFilter, FilterDepends(IonChannelModelingCampaignFilter)
]
