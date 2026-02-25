from typing import Annotated

from app.db.model import Campaign
from app.db.types import TaskType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.task_config import NestedTaskConfigFilter, NestedTaskConfigFilterDep


class CampaignFilter(CustomFilter, EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin):
    task_type: TaskType | None = None
    task_config: Annotated[
        NestedTaskConfigFilter | None,
        NestedTaskConfigFilterDep,
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Campaign
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


CampaignFilterDep = Annotated[CampaignFilter, FilterDepends(CampaignFilter)]
