from typing import Annotated

from app.db.model import AnalysisNotebookResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class NestedAnalysisNotebookResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookResult


class AnalysisNotebookResultFilter(
    EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookResult
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
        ]


AnalysisNotebookResultFilterDep = Annotated[
    AnalysisNotebookResultFilter, FilterDepends(AnalysisNotebookResultFilter)
]
