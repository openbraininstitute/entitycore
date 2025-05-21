import uuid
from typing import Annotated

from fastapi_filter import FilterDepends

from app.db.model import ValidationResult
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin


class ValidationResultFilter(
    CustomFilter,
    EntityFilterMixin,
):
    passed: bool | None = None
    validated_entity_id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ValidationResult
        ordering_model_fields = ["name"]  # noqa: RUF012


ValidationResultFilterDep = Annotated[ValidationResultFilter, FilterDepends(ValidationResultFilter)]
