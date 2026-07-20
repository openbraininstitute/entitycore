from typing import Annotated

from app.db.model import IonChannelModelingCampaign
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.ion_channel_modeling_config import (
    NestedIonChannelModelingConfigFilter,
    NestedIonChannelModelingConfigFilterDep,
)


class IonChannelModelingCampaignFilter(
    CustomFilter, EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin
):
    ion_channel_modeling_config: Annotated[
        NestedIonChannelModelingConfigFilter | None,
        NestedIonChannelModelingConfigFilterDep,
    ] = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingCampaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]


IonChannelModelingCampaignFilterDep = Annotated[
    IonChannelModelingCampaignFilter, FilterDepends(IonChannelModelingCampaignFilter)
]
