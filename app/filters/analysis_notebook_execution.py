from typing import Annotated

from app.db.model import AnalysisNotebookExecution
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin, ExecutionActivityFilterMixin
from app.filters.base import CustomFilter


class AnalysisNotebookExecutionFilter(
    CustomFilter, ActivityFilterMixin, ExecutionActivityFilterMixin
):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    status: str | None = None

    class Constants(CustomFilter.Constants):
        model = AnalysisNotebookExecution
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


AnalysisNotebookExecutionFilterDep = Annotated[
    AnalysisNotebookExecutionFilter, FilterDepends(AnalysisNotebookExecutionFilter)
]
