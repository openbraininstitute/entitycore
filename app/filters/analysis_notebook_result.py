from typing import Annotated

from app.db.model import AnalysisNotebookResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class NestedAnalysisNotebookResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookResult


class AnalysisNotebookResultFilter(EntityFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookResult
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
        ]


AnalysisNotebookResultFilterDep = Annotated[
    AnalysisNotebookResultFilter, FilterDepends(AnalysisNotebookResultFilter)
]
