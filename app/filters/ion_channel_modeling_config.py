import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import IonChannelModelingConfig
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class IonChannelModelingConfigFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    pass


class NestedIonChannelModelingConfigFilter(IonChannelModelingConfigFilterBase):
    class Constants(CustomFilter.Constants):
        model = IonChannelModelingConfig


class IonChannelModelingConfigFilter(
    EntityFilterMixin, IonChannelModelingConfigFilterBase, ILikeSearchFilterMixin
):
    ion_channel_modeling_campaign_id: uuid.UUID | None = None
    ion_channel_modeling_campaign_id__in: list[uuid.UUID] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingConfig
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


IonChannelModelingConfigFilterDep = Annotated[
    IonChannelModelingConfigFilter, FilterDepends(IonChannelModelingConfigFilter)
]
NestedIonChannelModelingConfigFilterDep = FilterDepends(
    with_prefix("ion_channel_modeling_config", NestedIonChannelModelingConfigFilter)
)
