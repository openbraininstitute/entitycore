import uuid
from typing import Annotated

from app.db.model import ValidationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import EntityFilterMixin, NameFilterMixin


class ValidationResultFilter(
    CustomFilter,
    EntityFilterMixin,
    NameFilterMixin,
):
    passed: bool | None = None
    validated_entity_id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ValidationResult
        ordering_model_fields = ["name"]  # noqa: RUF012


ValidationResultFilterDep = Annotated[ValidationResultFilter, FilterDepends(ValidationResultFilter)]
