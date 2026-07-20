from typing import Annotated

from app.db.model import Calibration
from app.dependencies.filter import FilterDepends
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class CalibrationFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Calibration
        ordering_model_fields = ["creation_date", "update_date"]  # ruff:ignore[mutable-class-default]


CalibrationFilterDep = Annotated[CalibrationFilter, FilterDepends(CalibrationFilter)]
