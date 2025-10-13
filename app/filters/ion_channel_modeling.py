import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import IonChannelModeling
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, IdFilterMixin, NameFilterMixin


class IonChannelModelingFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    pass


class NestedIonChannelModelingFilter(IonChannelModelingFilterBase):
    class Constants(CustomFilter.Constants):
        model = IonChannelModeling


class IonChannelModelingFilter(EntityFilterMixin, IonChannelModelingFilterBase):
    ion_channel_modeling_campaign_id: uuid.UUID | None = None
    ion_channel_modeling_campaign_id__in: list[uuid.UUID] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannelModeling
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


IonChannelModelingFilterDep = Annotated[IonChannelModelingFilter, FilterDepends(IonChannelModelingFilter)]
NestedIonChannelModelingFilterDep = FilterDepends(with_prefix("ion_channel_modeling", NestedIonChannelModelingFilter))
