import uuid

from app.db.model import IonChannelModelingConfig
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

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingConfig
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]
