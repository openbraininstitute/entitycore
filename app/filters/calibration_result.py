import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import CalibrationResult
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin


class CalibrationResultFilter(
    CustomFilter,
    EntityFilterMixin,
):
    value: float | None = None
    validated_entity_id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = CalibrationResult
        ordering_model_fields = ["name"]  # noqa: RUF012


CalibrationResultFilterDep = Annotated[
    CalibrationResultFilter, FilterDepends(CalibrationResultFilter)
]
