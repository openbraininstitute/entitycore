from typing import Annotated

from app.db.model import AnalysisNotebookEnvironment
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin
from app.filters.entity import EntityFilterMixin


class NestedAnalysisNotebookEnvironmentFilter(IdFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookEnvironment


class AnalysisNotebookEnvironmentFilter(EntityFilterMixin, CustomFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookEnvironment
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


AnalysisNotebookEnvironmentFilterDep = Annotated[
    AnalysisNotebookEnvironmentFilter, FilterDepends(AnalysisNotebookEnvironmentFilter)
]
