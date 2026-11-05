import uuid
from typing import Annotated

from app.db.model import ValidationResult
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import IdFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin


class NestedValidationResultFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    passed: bool | None = None

    class Constants(CustomFilter.Constants):
        model = ValidationResult


class ValidationResultFilter(
    CustomFilter,
    EntityFilterMixin,
    NameFilterMixin,
):
    passed: bool | None = None
    validated_entity_id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = ValidationResult
        ordering_model_fields = ["name"]  # ruff:ignore[mutable-class-default]


ValidationResultFilterDep = Annotated[ValidationResultFilter, FilterDepends(ValidationResultFilter)]
