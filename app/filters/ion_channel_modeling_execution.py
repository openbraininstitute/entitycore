from typing import Annotated

from app.db.model import IonChannelModelingExecution
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class IonChannelModelingExecutionFilter(
    CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingExecution
        ordering_model_fields = ["creation_date", "update_date"]  # ruff:ignore[mutable-class-default]


IonChannelModelingExecutionFilterDep = Annotated[
    IonChannelModelingExecutionFilter, FilterDepends(IonChannelModelingExecutionFilter)
]
