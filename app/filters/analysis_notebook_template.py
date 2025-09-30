from typing import Annotated

from app.db.model import AnalysisNotebookTemplate
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import (
    EntityFilterMixin,
    IdFilterMixin,
    NameFilterMixin,
)


class NestedAnalysisNotebookTemplateFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookTemplate


class AnalysisNotebookTemplateFilter(EntityFilterMixin, NameFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookTemplate
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
        ]


AnalysisNotebookTemplateFilterDep = Annotated[
    AnalysisNotebookTemplateFilter, FilterDepends(AnalysisNotebookTemplateFilter)
]
