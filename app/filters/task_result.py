# app/filters/task_result
from typing import Annotated

from app.db.model import TaskResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class TaskResultFilter(EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = TaskResult
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


TaskResultFilterDep = Annotated[TaskResultFilter, FilterDepends(TaskResultFilter)]
