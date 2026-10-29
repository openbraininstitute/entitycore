from typing import Annotated

from app.db.model import ResearchLog
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class ResearchLogFilter(EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = ResearchLog
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
        ]


ResearchLogFilterDep = Annotated[ResearchLogFilter, FilterDepends(ResearchLogFilter)]
