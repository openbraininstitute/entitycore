from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import IonChannel
from app.filters.base import CustomFilter
from app.filters.common import CreationFilterMixin, CreatorFilterMixin, IdFilterMixin


class IonChannelFilter(
    CustomFilter,
    IdFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
):
    label: str
    gene: str

    order_by: list[str] = ["label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannel
        ordering_model_fields = ["label"]  # noqa: RUF012


IonChannelFilterDep = Annotated[IonChannelFilter, FilterDepends(IonChannelFilter)]
