import uuid
from typing import Annotated

from app.db.model import MEModelCalibrationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.entity import EntityFilterMixin


class MEModelCalibrationResultFilter(
    CustomFilter,
    EntityFilterMixin,
):
    passed: bool | None = None
    calibrated_entity_id: uuid.UUID | None = None

    order_by: list[str] = ["calibrated_entity_id"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MEModelCalibrationResult
        ordering_model_fields = ["calibrated_entity_id"]  # noqa: RUF012


MEModelCalibrationResultFilterDep = Annotated[
    MEModelCalibrationResultFilter, FilterDepends(MEModelCalibrationResultFilter)
]
