import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import TaskConfig
from app.db.types import TaskConfigType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class TaskConfigFilterBase(NameFilterMixin, IdFilterMixin, CustomFilter):
    task_config_type: TaskConfigType | None = None


class NestedTaskConfigFilter(TaskConfigFilterBase):
    class Constants(CustomFilter.Constants):
        model = TaskConfig


class TaskConfigFilter(EntityFilterMixin, TaskConfigFilterBase, ILikeSearchFilterMixin):
    task_config_generator_id: uuid.UUID | None = None
    task_config_generator_id__in: list[uuid.UUID] | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = TaskConfig
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


TaskConfigFilterDep = Annotated[TaskConfigFilter, FilterDepends(TaskConfigFilter)]
NestedTaskConfigFilterDep = FilterDepends(with_prefix("task_config", NestedTaskConfigFilter))
