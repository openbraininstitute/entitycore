from typing import Annotated

from app.db.model import TaskExecution
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class TaskExecutionFilter(CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = TaskExecution
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


TaskExecutionFilterDep = Annotated[TaskExecutionFilter, FilterDepends(TaskExecutionFilter)]
