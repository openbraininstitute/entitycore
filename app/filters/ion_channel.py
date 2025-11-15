from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import IonChannel
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    CreationFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
)
from app.filters.person import CreatorFilterMixin


class IonChannelFilterMixin(
    IdFilterMixin,
    NameFilterMixin,
):
    label: str | None = None
    gene: str | None = None


class NestedIonChannelFilter(
    CustomFilter,
    IonChannelFilterMixin,
):
    class Constants(CustomFilter.Constants):
        model = IonChannel


class IonChannelFilter(
    CustomFilter,
    IonChannelFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
):
    order_by: list[str] = ["label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = IonChannel
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "label",
            "name",
        ]


IonChannelFilterDep = Annotated[IonChannelFilter, FilterDepends(IonChannelFilter)]
NestedIonChannelFilterDep = FilterDepends(with_prefix("ion_channel", NestedIonChannelFilter))
