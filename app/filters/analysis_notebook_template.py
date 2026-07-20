from typing import Annotated

from app.db.model import AnalysisNotebookTemplate
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    IdFilterMixin,
    ILikeSearchFilterMixin,
    NameFilterMixin,
)
from app.filters.entity import EntityFilterMixin


class NestedAnalysisNotebookTemplateFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookTemplate


class AnalysisNotebookTemplateFilter(
    EntityFilterMixin, NameFilterMixin, ILikeSearchFilterMixin, CustomFilter
):
    assignment_id: str | None = None
    assignment_id__in: list[str] | None = None
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookTemplate
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
        ]


AnalysisNotebookTemplateFilterDep = Annotated[
    AnalysisNotebookTemplateFilter, FilterDepends(AnalysisNotebookTemplateFilter)
]
