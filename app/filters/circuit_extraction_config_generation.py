from typing import Annotated

from app.db.model import CircuitExtractionConfigGeneration
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class CircuitExtractionConfigGenerationFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CircuitExtractionConfigGeneration
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


CircuitExtractionConfigGenerationFilterDep = Annotated[
    CircuitExtractionConfigGenerationFilter, FilterDepends(CircuitExtractionConfigGenerationFilter)
]
