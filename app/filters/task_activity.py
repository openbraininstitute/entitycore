from typing import Annotated

from app.db.model import TaskActivity
from app.db.types import TaskActivityType
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class TaskActivityFilter(CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin):
    task_activity_type: TaskActivityType | None = None
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = TaskActivity
        ordering_model_fields = ["creation_date", "update_date"]  # ruff:ignore[mutable-class-default]


TaskActivityFilterDep = Annotated[TaskActivityFilter, FilterDepends(TaskActivityFilter)]
